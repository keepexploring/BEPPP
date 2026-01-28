# PPP and Socket C Source Code Analysis
## Complete Implementation Details for Pico 2 Firmware

This document contains the actual C source code implementations of PPP and socket functions used by the battery firmware on Raspberry Pi Pico 2.

---

## Overview

The battery firmware uses this call stack for network operations:

```
Python (cebattery.py)
    ↓
MicroPython LTE.py wrapper
    ↓
MicroPython network_ppp_lwip.c (RP2 port)
    ↓
LWIP PPP stack (ppp.c)
    ↓
LWIP Socket stack (modlwip.c)
```

---

## 1. MicroPython PPP Wrappers (RP2 Port)

**Source**: [micropython/extmod/network_ppp_lwip.c](https://github.com/micropython/micropython/blob/master/extmod/network_ppp_lwip.c)

The Raspberry Pi Pico 2 (RP2350) uses the generic LWIP PPP implementation from `extmod/network_ppp_lwip.c`.

### 1.1 network_ppp_connect() - Python PPP.connect() Implementation

This is the C function that gets called when Python code executes `self._ppp.connect()`:

```c
static mp_obj_t network_ppp_connect(size_t n_args, const mp_obj_t *args, mp_map_t *kw_args) {
    // Parse arguments (authentication, timeout, etc.)
    enum { ARG_security, ARG_user, ARG_key };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_security, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = PPPAUTHTYPE_NONE} },
        { MP_QSTR_user, MP_ARG_KW_ONLY | MP_ARG_OBJ, {.u_obj = mp_const_none} },
        { MP_QSTR_key, MP_ARG_KW_ONLY | MP_ARG_OBJ, {.u_obj = mp_const_none} },
    };
    mp_arg_val_t parsed_args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args - 1, args + 1, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, parsed_args);

    network_ppp_obj_t *self = MP_OBJ_TO_PTR(args[0]);

    // Create PPP control block if this is the first connection attempt
    if (self->state == STATE_INACTIVE) {
        self->pcb = pppos_create(&self->netif, network_ppp_output_callback,
                                 network_ppp_status_cb, self);
        if (self->pcb == NULL) {
            mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("pppos_create failed"));
        }
        self->state = STATE_ACTIVE;
        network_ppp_stream_uart_irq_enable(self);
    }

    // Check if already connecting or connected
    if (self->state == STATE_CONNECTING || self->state == STATE_CONNECTED) {
        mp_raise_OSError(MP_EALREADY);  // Raises "Already in progress" error
    }

    // Set up authentication if credentials provided
    if (parsed_args[ARG_security].u_int != PPPAUTHTYPE_NONE) {
        const char *user_str = mp_obj_str_get_str(parsed_args[ARG_user].u_obj);
        const char *key_str = mp_obj_str_get_str(parsed_args[ARG_key].u_obj);
        ppp_set_auth(self->pcb, parsed_args[ARG_security].u_int, user_str, key_str);
    }

    ppp_set_default(self->pcb);
    ppp_set_usepeerdns(self->pcb, true);

    // *** CRITICAL CALL: This initiates the PPP connection ***
    if (ppp_connect(self->pcb, 0) != ERR_OK) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("ppp_connect failed"));
    }

    self->state = STATE_CONNECTING;

    // Poll once in case there's data waiting
    network_ppp_poll(1, args);

    return mp_const_none;
}
```

**Key Observations:**
- Creates PPP control block (`self->pcb`) on first connection
- Raises `MP_EALREADY` error if already connecting/connected (prevents double-connect)
- Sets state to `STATE_CONNECTING` before returning
- **Returns immediately** - connection happens asynchronously
- The actual wait for connection happens in Python code: `while self._ppp.status() != 4:`

---

### 1.2 network_ppp_disconnect() - Python PPP.disconnect() Implementation

This is the C function that gets called when Python code executes `self._ppp.disconnect()`:

```c
static mp_obj_t network_ppp_disconnect(mp_obj_t self_in) {
    network_ppp_obj_t *self = MP_OBJ_TO_PTR(self_in);

    // *** CRITICAL SAFETY CHECK: Only disconnect if actively connecting or connected ***
    if (self->state == STATE_CONNECTING || self->state == STATE_CONNECTED) {
        // Initiate close and wait for PPPERR_USER callback
        ppp_close(self->pcb, 0);
    }

    // If not connecting/connected, just return silently (no error)
    return mp_const_none;
}
```

**Key Observations:**
- ✅ **SAFE**: Only calls `ppp_close()` if state is `STATE_CONNECTING` or `STATE_CONNECTED`
- ✅ **SAFE**: Silently returns if called in other states (no error, no crash)
- ✅ **SAFE**: Safe to call even if `connect()` failed partway through
- ✅ **SAFE**: Safe to call multiple times (idempotent)

**Conclusion**: The MicroPython wrapper is extremely defensive. You can call `disconnect()` at any time without crashing.

---

## 2. LWIP PPP Core Functions

**Source**: [lwip-tcpip/lwip/src/netif/ppp/ppp.c](https://github.com/lwip-tcpip/lwip/blob/master/src/netif/ppp/ppp.c)

The MicroPython wrappers above call into the LWIP (Lightweight IP) TCP/IP stack. Here are the underlying implementations:

### 2.1 ppp_connect() - LWIP Core Connection Function

This is the actual LWIP function called by `network_ppp_connect()` above:

```c
err_t ppp_connect(ppp_pcb *pcb, u16_t holdoff) {
  LWIP_ASSERT_CORE_LOCKED();

  // *** CRITICAL CHECK: Can only connect if PPP is in DEAD phase ***
  if (pcb->phase != PPP_PHASE_DEAD) {
    return ERR_ALREADY;  // Already active/connecting/connected
  }

  PPPDEBUG(LOG_DEBUG, ("ppp_connect[%d]: holdoff=%d\n", pcb->netif->num, holdoff));

  magic_randomize();

  // If no holdoff delay, connect immediately
  if (holdoff == 0) {
    ppp_do_connect(pcb);  // *** Starts the actual connection process ***
    return ERR_OK;
  }

  // Otherwise, schedule connection after holdoff delay
  new_phase(pcb, PPP_PHASE_HOLDOFF);
  sys_timeout((u32_t)(holdoff*1000), ppp_do_connect, pcb);
  return ERR_OK;
}
```

**Key Observations:**
- Returns `ERR_ALREADY` if PPP is not in `PPP_PHASE_DEAD` (already active)
- With `holdoff=0` (as used by MicroPython), connects immediately via `ppp_do_connect()`
- **Connection is asynchronous** - this function returns immediately
- Actual PPP handshake happens in background via `ppp_do_connect()`
- The Python code must poll `status()` to know when connection completes

**PPP Phases**:
1. `PPP_PHASE_DEAD` - Not connected, ready to connect
2. `PPP_PHASE_HOLDOFF` - Waiting before connection attempt
3. `PPP_PHASE_INITIALIZE` - Starting connection
4. `PPP_PHASE_ESTABLISH` - LCP negotiation in progress
5. `PPP_PHASE_AUTHENTICATE` - Authentication in progress
6. `PPP_PHASE_NETWORK` - Network protocol negotiation (IPCP)
7. `PPP_PHASE_RUNNING` - **Fully connected** (status = 4)
8. `PPP_PHASE_TERMINATE` - Shutting down connection
9. Back to `PPP_PHASE_DEAD`

---

### 2.2 ppp_close() - LWIP Core Disconnect Function

This is the actual LWIP function called by `network_ppp_disconnect()` above:

```c
err_t ppp_close(ppp_pcb *pcb, u8_t nocarrier)
{
  LWIP_ASSERT_CORE_LOCKED();

  pcb->err_code = PPPERR_USER;  // Mark as user-requested close

  // *** CASE 1: In holdoff phase (waiting to connect) ***
  if (pcb->phase == PPP_PHASE_HOLDOFF) {
    sys_untimeout(ppp_do_connect, pcb);  // Cancel scheduled connection
    new_phase(pcb, PPP_PHASE_DEAD);
  }

  // *** CASE 2: Already in dead phase (not connected) ***
  if (pcb->phase == PPP_PHASE_DEAD) {
    pcb->link_status_cb(pcb, pcb->err_code, pcb->ctx_cb);  // Just call status callback
    return ERR_OK;  // Nothing to do, return success
  }

  // *** CASE 3: Already terminating ***
  if (pcb->phase >= PPP_PHASE_TERMINATE) {
    return ERR_INPROGRESS;  // Already shutting down, return in-progress (not an error)
  }

  // *** CASE 4: Connection not yet established (early phase) ***
  if (pcb->phase < PPP_PHASE_ESTABLISH) {
    new_phase(pcb, PPP_PHASE_DISCONNECT);
    ppp_link_terminated(pcb);  // Clean up immediately
    return ERR_OK;
  }

  // *** CASE 5: Carrier lost while running ***
  if (nocarrier && pcb->phase == PPP_PHASE_RUNNING) {
    PPPDEBUG(LOG_DEBUG, ("ppp_close[%d]: carrier lost -> lcp_lowerdown\n", pcb->netif->num));
    lcp_lowerdown(pcb);
    link_terminated(pcb);
    return ERR_OK;
  }

  // *** CASE 6: Normal close - send LCP terminate request ***
  PPPDEBUG(LOG_DEBUG, ("ppp_close[%d]: kill_link -> lcp_close\n", pcb->netif->num));
  lcp_close(pcb, "User request");  // Send proper PPP termination
  return ERR_OK;
}
```

**Key Observations:**
- ✅ **SAFE**: Handles **all 9 PPP phases** gracefully with specific logic for each
- ✅ **SAFE**: If already in `DEAD` phase, just calls status callback and returns `ERR_OK`
- ✅ **SAFE**: If already terminating, returns `ERR_INPROGRESS` (not an error condition)
- ✅ **SAFE**: Can be called at **ANY time** in **ANY state** without crashing
- ✅ **SAFE**: Properly cleans up resources regardless of which phase PPP is in
- ✅ **SAFE**: Safe to call multiple times (idempotent)

**Conclusion**: Both the MicroPython wrappers AND the underlying LWIP functions are extremely robust and defensive. You can safely call `disconnect()` even if `connect()` never completed or failed partway through.

---

## 3. Socket Timeout Implementation (RP2 Port)

**Source**: [micropython/extmod/modlwip.c](https://github.com/micropython/micropython/blob/master/extmod/modlwip.c)

The RP2 Pico uses LWIP for its socket implementation. Here's how timeouts work:

### 3.1 Socket Timeout for connect()

```c
// From lwip_socket_connect() function in modlwip.c

mp_uint_t ticks_start = mp_hal_ticks_ms();

// Wait for connection to complete or fail
for (;;) {
    poll_sockets();  // Process network events

    // Check if connection completed (success or failure)
    if (socket->state != STATE_CONNECTING) {
        break;
    }

    // *** CHECK TIMEOUT: Applies to ENTIRE connect() operation ***
    if (socket_is_timedout(socket, ticks_start)) {
        mp_raise_OSError(MP_ETIMEDOUT);  // Raises timeout exception
    }

    // Yield to other tasks
    MICROPY_EVENT_POLL_HOOK;
}
```

**Key Observations:**
- ✅ Timeout applies to the **entire connection attempt** (not just initial SYN)
- ✅ Raises `MP_ETIMEDOUT` exception if timeout expires
- ✅ The timeout parameter in `requests.post(..., timeout=20)` **WORKS CORRECTLY**

---

### 3.2 Socket Timeout for recv() / read()

```c
// From lwip_socket_recv() function in modlwip.c

mp_uint_t start = mp_hal_ticks_ms();

// Wait for data to arrive
while (socket->incoming.tcp.pbuf == NULL) {
    // *** CHECK TIMEOUT: Covers ENTIRE read operation ***
    if (socket->timeout != -1 &&
        mp_hal_ticks_ms() - start > socket->timeout) {
        return -1;  // Timeout - return error
    }

    poll_sockets();  // Process network events
    MICROPY_EVENT_POLL_HOOK;
}

// Data arrived, read it
// ... (pbuf processing code)
```

**Key Observations:**
- ✅ Timeout applies to the **entire recv() operation** (not just initial check)
- ✅ Returns `-1` on timeout (converted to exception at higher level)
- ✅ Properly handles case where server stops sending data mid-response

---

### 3.3 Socket Timeout for send() / write()

```c
// From lwip_socket_send() function in modlwip.c

// Note: Timeout only applies to INITIAL buffer availability
// Does NOT guarantee the data is actually transmitted within timeout period

mp_uint_t start = mp_hal_ticks_ms();

while (socket->tcp.pcb->state == ESTABLISHED &&
       tcp_sndbuf(socket->tcp.pcb) == 0) {
    // Wait for send buffer space
    if (socket->timeout != -1 &&
        mp_hal_ticks_ms() - start > socket->timeout) {
        return -1;  // Timeout waiting for buffer space
    }

    poll_sockets();
    MICROPY_EVENT_POLL_HOOK;
}

// Buffer space available, write data
tcp_write(socket->tcp.pcb, buf, len, TCP_WRITE_FLAG_COPY);
```

**Key Observations:**
- ⚠️ Timeout only applies to **initial buffer availability**, NOT transmission completion
- ⚠️ Data may still be "in flight" when send() returns
- ✅ This is standard socket behavior (same as Linux/BSD)

---

## 4. Conclusions & Findings

### ✅ Socket Timeout WORKS on RP2 Pico

The LWIP socket implementation on Pico 2 **fully supports timeouts**:
- **connect()**: Timeout applies to entire connection attempt ✅
- **recv()**: Timeout applies to entire read operation ✅
- **send()**: Timeout applies to buffer availability (standard behavior) ⚠️

**Verdict**: The `requests.post(..., timeout=20)` calls in `cebattery.py` **ARE working correctly**. Socket timeouts are NOT the cause of the firmware hang.

---

### ✅ PPP disconnect() is SAFE

Both MicroPython and LWIP implementations are extremely defensive:
- Only disconnects if in `CONNECTING` or `CONNECTED` state
- Silently returns if called in other states (no crash)
- Handles all PPP phases gracefully
- Safe to call multiple times
- Safe to call even if `connect()` failed

**Verdict**: Calling `stop_ppp()` in the `finally` block (line 678 of cebattery.py) is **completely safe**, even if `start_ppp()` failed. This is NOT the cause of the hang.

---

### 🚨 ACTUAL BUG: Infinite Loop in Pico 2 LTE.py

**Source**: [pimoroni-pico-rp2350/lte.py](https://github.com/pimoroni/pimoroni-pico-rp2350/blob/feature/can-haz-ppp-plz/micropython/modules_py/lte.py)

The Pico 2 version of `lte.py` has an **infinite loop with NO timeout**:

```python
def start_ppp(self, baudrate=DEFAULT_UART_BAUD, connect=True):
    # ... setup code ...

    self._ppp = PPP(self._uart)
    self._ppp.connect()

    # *** BUG: INFINITE LOOP - NO TIMEOUT! ***
    while self._ppp.status() != 4:
        time.sleep(1.0)  # Will loop forever if status never becomes 4

    return self._ppp.ifconfig()
```

**This is a REGRESSION** - the Pico 1 version had a proper timeout:

```python
def start_ppp(self, baudrate=DEFAULT_UART_BAUD, connect=True, timeout=60):
    # ... setup code ...

    self._ppp = PPP(self._uart)
    self._ppp.connect()

    # ✅ HAD TIMEOUT in Pico 1 version
    giveup = time.time() + timeout
    while self._ppp.status() != 4:
        if time.time() > giveup:
            raise CellularError("timed out starting ppp")
        time.sleep(1.0)

    return self._ppp.ifconfig()
```

---

## 5. Recommended Fix

**File**: `hardware/battery-firmware-v6.0-source-code/modules_py/lte.py`

**Add timeout back to start_ppp():**

```python
def start_ppp(self, baudrate=DEFAULT_UART_BAUD, connect=True, timeout=60):
    self._wait_ready(poll_time=1.0, timeout=30)

    # Switch to a faster baudrate
    self._send_at_command(f"AT+IPR={baudrate}")
    self._flush_uart()
    self._uart.init(
        baudrate=baudrate,
        timeout=DEFAULT_UART_TIMEOUT,
        timeout_char=DEFAULT_UART_TIMEOUT_CHAR,
        rxbuf=DEFAULT_UART_RXBUF)
    self._wait_ready(poll_time=1.0)

    if connect:
        self.connect()

    self._flush_uart()
    self._uart.write("ATD*99#\r")
    self._uart.flush()

    self._ppp = PPP(self._uart)
    self._ppp.connect()

    # *** FIX: Add timeout to prevent infinite loop ***
    giveup = time.time() + timeout
    while self._ppp.status() != 4:
        if time.time() > giveup:
            raise CellularError("timed out starting ppp")
        time.sleep(1.0)

    return self._ppp.ifconfig()
```

This matches the original Pico 1 implementation and will prevent the firmware from hanging forever when PPP fails to reach the `RUNNING` state (status 4).

---

## 6. Source Code References

All analysis backed by actual C and Python source code:

- **MicroPython PPP (RP2)**: [extmod/network_ppp_lwip.c](https://github.com/micropython/micropython/blob/master/extmod/network_ppp_lwip.c)
- **LWIP PPP Core**: [lwip/src/netif/ppp/ppp.c](https://github.com/lwip-tcpip/lwip/blob/master/src/netif/ppp/ppp.c)
- **MicroPython Socket (RP2)**: [extmod/modlwip.c](https://github.com/micropython/micropython/blob/master/extmod/modlwip.c)
- **Pico 2 LTE.py (buggy)**: [pimoroni-pico-rp2350/lte.py](https://github.com/pimoroni/pimoroni-pico-rp2350/blob/feature/can-haz-ppp-plz/micropython/modules_py/lte.py)
- **MicroPython PPP Docs**: [network.PPP](https://docs.micropython.org/en/latest/library/network.PPP.html)

---

**Document Created**: 2026-01-28
**Analysis By**: Claude Code (Sonnet 4.5)
**Battery Firmware Version**: v6.0 (Pico 2 / RP2350)
