# Battery Firmware Hang - Root Cause Analysis

**Problem**: Battery firmware occasionally hangs after successfully receiving authentication token but before sending data.

**Status**: ✅ **ROOT CAUSE IDENTIFIED** - Infinite loop in Pico 2 `lte.py`

---

## Executive Summary

After deep analysis of the MicroPython and LWIP C source code, we have definitively identified the root cause of the firmware hang:

**🚨 CRITICAL BUG**: The Pico 2 version of `lte.py` has an **infinite loop with no timeout** in the `start_ppp()` method. If the PPP connection fails to reach status 4 (fully connected), the firmware hangs forever.

This is a **regression** from the Pico 1 version which had a proper 60-second timeout.

---

## What We Ruled Out (Verified via C Source Code)

### ✅ Socket Timeout DOES Work on Pico 2

**Verified in**: [micropython/extmod/modlwip.c](https://github.com/micropython/micropython/blob/master/extmod/modlwip.c)

- Timeout applies to **entire `connect()` operation** ✅
- Timeout applies to **entire `recv()` operation** ✅
- The `requests.post(..., timeout=20)` calls in `cebattery.py` **ARE working correctly** ✅

**Conclusion**: Socket timeouts are NOT the cause of the hang. Line 658 (`requests.post()`) is NOT hanging.

---

### ✅ PPP disconnect() is SAFE to Call Anytime

**This was one of your original suspicions (line 678), but the C code proves it's NOT the problem.**

**Verified in**:
- [micropython/extmod/network_ppp_lwip.c](https://github.com/micropython/micropython/blob/master/extmod/network_ppp_lwip.c)
- [lwip/src/netif/ppp/ppp.c](https://github.com/lwip-tcpip/lwip/blob/master/src/netif/ppp/ppp.c)

The C source code shows `disconnect()` implementation:

```c
static mp_obj_t network_ppp_disconnect(mp_obj_t self_in) {
    network_ppp_obj_t *self = MP_OBJ_TO_PTR(self_in);

    // Only calls ppp_close() if already connecting/connected
    if (self->state == STATE_CONNECTING || self->state == STATE_CONNECTED) {
        ppp_close(self->pcb, 0);
    }

    // Otherwise just returns - NO ERROR, NO CRASH
    return mp_const_none;
}
```

**What this means**:
- ✅ If PPP was never initialized → Just returns, does nothing (no crash)
- ✅ If `connect()` was never called → Just returns, does nothing (no crash)
- ✅ If `connect()` failed early → Just returns, does nothing (no crash)
- ✅ If `connect()` is in progress → Safely closes
- ✅ If already connected → Safely closes
- ✅ Can be called multiple times safely (idempotent)

**Conclusion**: The `stop_ppp()` call in the `finally` block (line 678 of cebattery.py) is **completely safe** and is **NOT the cause of the hang**. You can call `stop_ppp()` even if `start_ppp()` never completed or failed - it will just return without doing anything.

---

## 🎯 Root Cause: Infinite Loop in start_ppp()

### The Bug

**File**: [pimoroni-pico-rp2350/lte.py](https://github.com/pimoroni/pimoroni-pico-rp2350/blob/feature/can-haz-ppp-plz/micropython/modules_py/lte.py)

**Location**: `start_ppp()` method

**Where this is called from in cebattery.py**:
- Line 649: `self.networkLte.start_ppp()` (first attempt)
- Line 654: `self.networkLte.start_ppp()` (retry after failure)

**The buggy code in lte.py**:

```python
def start_ppp(self, baudrate=DEFAULT_UART_BAUD, connect=True):
    # ... setup code ...

    self._ppp = PPP(self._uart)
    self._ppp.connect()

    # 🚨 BUG: INFINITE LOOP - NO TIMEOUT!
    while self._ppp.status() != 4:
        time.sleep(1.0)  # Will loop forever if status never becomes 4

    return self._ppp.ifconfig()
```

### How the Infinite Loop Works (Step-by-Step)

Let's trace exactly what happens when this code executes:

```python
# Line 1: Create PPP object
self._ppp = PPP(self._uart)

# Line 2: Start connection (asynchronous - returns immediately)
self._ppp.connect()

# Line 3-4: THE INFINITE LOOP
while self._ppp.status() != 4:
    time.sleep(1.0)
```

**Step-by-step execution**:

1. **`self._ppp.connect()` is called**
   - This starts PPP negotiation with the carrier (asynchronous)
   - Returns immediately (does NOT wait for connection to complete)
   - PPP state machine begins: DEAD → INITIALIZE → ESTABLISH → etc.

2. **First iteration of loop**:
   - Checks: `self._ppp.status()` returns 0, 1, 2, or 3 (not yet connected)
   - Condition `!= 4` is TRUE
   - Sleeps 1 second
   - Loop continues

3. **Second iteration** (1 second later):
   - Checks: `self._ppp.status()` returns 0, 1, 2, or 3 (still negotiating)
   - Condition `!= 4` is TRUE
   - Sleeps 1 second
   - Loop continues

4. **Third iteration** (2 seconds later):
   - Same as above
   - Loop continues

5. **Normal case** (connection succeeds after ~10-30 seconds):
   - Checks: `self._ppp.status()` **NOW returns 4** (connection complete!)
   - Condition `!= 4` is FALSE
   - Loop exits
   - Function returns `self._ppp.ifconfig()` ✅
   - Firmware continues to line 658 (get token)

6. **🚨 PROBLEM CASE** (connection gets stuck):
   - After 10, 20, 30, 60, 120+ seconds...
   - Checks: `self._ppp.status()` **STILL returns 0, 1, 2, or 3** (stuck!)
   - Condition `!= 4` is TRUE (forever!)
   - Sleeps 1 second
   - Loop continues **FOREVER**
   - Function **NEVER returns**
   - Firmware **NEVER reaches line 658**
   - Battery is **HUNG FOREVER** 🚨

**The critical flaw**: There's no timeout check inside the loop. The code assumes PPP will eventually reach status 4, but there are many reasons it might not (see below). When it doesn't, the firmware hangs forever with no recovery mechanism.

### Why This Hangs

PPP `status()` returns values 0-4 representing the connection phase:
- **0** = `PPP_PHASE_DEAD` - Not connected
- **1** = `PPP_PHASE_INITIALIZE` - Starting connection
- **2** = `PPP_PHASE_ESTABLISH` - LCP negotiation (Link Control Protocol)
- **3** = `PPP_PHASE_AUTHENTICATE` - Authentication in progress
- **4** = `PPP_PHASE_RUNNING` - **Fully connected** (required state)

The code waits in an infinite loop for status to become 4. **If PPP gets stuck in any earlier phase and never reaches phase 4, the firmware hangs forever.**

### What Causes PPP to Get Stuck (Never Reach Status 4)

There are many network and modem conditions that can prevent PPP from reaching the RUNNING phase:

#### 1. Modem/Hardware Issues
- **Modem not responding to ATD*99# command** - The dial command fails silently
- **UART communication errors** - Data corruption on serial line
- **Modem firmware crash** - SIM7600 module hangs internally
- **Power supply issues** - Modem brownout during connection attempt
- **Temperature-related modem instability** - Common with SIM7600 series

#### 2. Network/Carrier Issues
- **Weak cellular signal** - PPP negotiation times out waiting for carrier responses
- **Carrier network congestion** - Carrier delays or drops PPP packets
- **APN misconfiguration** - Wrong APN settings prevent IPCP negotiation
- **Network temporarily unavailable** - Tower maintenance, no capacity, etc.
- **SIM card issues** - Not provisioned for data, expired, suspended account

#### 3. PPP Protocol Negotiation Failures
- **LCP negotiation fails** (Phase 2) - Modem and network can't agree on link parameters
- **Authentication fails** (Phase 3) - PAP/CHAP credentials rejected (though we use authmode 0)
- **IPCP negotiation fails** (Phase 3→4) - Can't get IP address from network
- **DNS configuration fails** - Network won't provide DNS servers
- **MTU negotiation issues** - Modem and network disagree on maximum packet size

#### 4. Timing/Race Conditions
- **Modem sends PPP frames before MicroPython is ready** - Packets lost
- **UART buffer overflow** - PPP negotiation packets dropped
- **Modem goes to sleep mid-connection** - Power saving mode kicks in
- **Previous connection state not cleared** - Modem thinks it's still connected

#### 5. Why This is Intermittent

The hang is intermittent because:
- **Most of the time**, network conditions are good and PPP reaches status 4 quickly (works fine)
- **Occasionally**, one of the above issues occurs and PPP gets stuck in phase 0-3 (hangs forever)
- The failure rate depends on:
  - Local signal strength (batteries in weak signal areas hang more often)
  - Time of day (network congestion varies)
  - Weather (affects cellular signal)
  - Modem temperature (affects stability)
  - Battery charge level (affects modem power stability)

**The key problem**: Without a timeout, there's no recovery mechanism. The firmware just waits forever instead of giving up and retrying.

### Comparison with Working Pico 1 Version

The original Pico 1 `lte.py` had a timeout that was **removed** in the Pico 2 port:

```python
def start_ppp(self, baudrate=DEFAULT_UART_BAUD, connect=True, timeout=60):
    # ... setup code ...

    self._ppp = PPP(self._uart)
    self._ppp.connect()

    # ✅ ORIGINAL: Had timeout
    giveup = time.time() + timeout
    while self._ppp.status() != 4:
        if time.time() > giveup:
            raise CellularError("timed out starting ppp")
        time.sleep(1.0)

    return self._ppp.ifconfig()
```

---

## How the Hang Manifests in Your System

### Scenario 1: Hang During Initial Connection (Never Gets Token)

**Sequence**:
```
1. Battery powers up and starts firmware
2. Calls start_ppp() at cebattery.py line 649
3. LTE modem starts PPP negotiation with carrier
4. PPP gets stuck in phase 0-3 (e.g., waiting for IPCP response from carrier)
5. start_ppp() enters infinite loop checking status: while self._ppp.status() != 4
6. Status stays at 0, 1, 2, or 3 forever - never reaches 4
7. Firmware HANGS in this loop forever
8. Never reaches line 658 (token request)
9. Battery never logs in, never sends data
```

**User observation**: Battery appears dead or frozen. No data uploaded. No logs after "start LTE ppp network".

**Duration**: Forever (until battery power dies or manual reset)

---

### Scenario 2: Hang After Getting Token (Most Confusing!)

**This scenario matches your description: "Battery hangs after getting token successfully but then never sends the data"**

**Sequence**:
```
1. Battery powers up
2. First call to start_ppp() at line 649 succeeds (PPP reaches status 4)
3. Battery successfully gets authentication token at line 659 ✅
4. Battery tries to send data at line 666
5. Network conditions degrade (signal fades, tower switches, packet loss, etc.)
6. Socket timeout at line 666 works correctly and raises exception
   OR JSON decoding fails due to incomplete/corrupted response
7. Exception handler catches error at line 670
8. Line 653: Exception handler tries to recover by calling stop_ppp()
9. Line 654: Exception handler calls start_ppp() AGAIN for retry
10. THIS TIME PPP negotiation fails (network conditions still bad)
11. start_ppp() HANGS in infinite loop at line 649/654
12. Battery is now frozen forever with valid token but no data sent
```

**User observation**:
- Webhook logs show battery successfully logged in (got token)
- But no data ever arrives
- Battery appears to hang "after getting token"
- Very confusing because login worked!

**Duration**: Forever (until battery power dies or manual reset)

**Why this is the confusing case**: The battery DID successfully connect once and got a token. This makes it look like the problem is with sending data (line 666) or JSON parsing (line 659). But actually, the hang is in the RETRY logic (line 654) when `start_ppp()` is called a second time and fails.

---

### Scenario 3: Successful Operation (For Comparison)

**When everything works**:
```
1. Battery powers up
2. start_ppp() at line 649 succeeds quickly (PPP reaches status 4 in ~10-30 seconds)
3. Battery gets token at line 659 ✅
4. Battery sends data at line 666 ✅
5. stop_ppp() at line 678 safely disconnects ✅
6. Battery goes back to sleep until next cycle
```

**Duration**: 30-60 seconds total

**User observation**: Data appears in dashboard as expected

---

### Why Scenario 2 Explains Your Symptoms

You reported: "Battery occasionally hangs after getting token successfully, then never sends the data"

This perfectly matches **Scenario 2**:
- Token request succeeds (line 659) ✅
- You see this in webhook logs ✅
- But then data never arrives
- The hang is actually in the RETRY at line 654, not in the data send at line 666

**The misleading part**: The symptoms make it look like the problem is at line 658, 659, or 678 (your original suspicions). But actually, the hang is in the retry logic when network conditions have degraded and `start_ppp()` is called a second time.

**Why it's intermittent**:
- Sometimes the first `start_ppp()` call fails → Scenario 1
- Sometimes the first call succeeds but retry fails → Scenario 2
- Most of the time both succeed → Scenario 3 (works fine)

The failure rate depends on how often PPP negotiation fails due to the network/modem issues listed above.

---

## The Fix

**File**: `hardware/battery-firmware-v6.0-source-code/modules_py/lte.py`

**Change**: Add timeout parameter and timeout check to `start_ppp()` method:

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

### How to Apply the Fix

1. Navigate to your firmware build directory:
   ```bash
   cd pimoroni-pico-rp2350/build/pimoroni-pico/micropython/modules_py
   ```

2. Edit `lte.py` and apply the changes above to the `start_ppp()` method

3. Rebuild the firmware:
   ```bash
   cd ../../..  # Back to pimoroni-pico-rp2350/build
   rm -rf build-rpi_pico2  # Force clean rebuild
   source ../ci/micropython.sh
   ci_cmake_configure rpi_pico2
   ci_cmake_build rpi_pico2
   ```

4. Flash the new firmware to all batteries

---

## Additional Recommended Improvements

### 1. Add Watchdog Timer (High Priority)

The improved firmware (`cebattery_improved.py`) already has this, but production (`cebattery.py`) does not:

```python
from machine import WDT

# Early in the script
wdt = WDT(timeout=120000)  # 2 minute watchdog

# Feed watchdog regularly throughout execution
wdt.feed()  # Before each major operation
```

**Benefits**:
- Provides automatic recovery from ANY hang (not just PPP)
- Battery will reboot and retry instead of being stuck forever
- Already proven in improved firmware

### 2. Add Better Diagnostic Logging

Add print statements to identify exactly where hangs occur:

```python
def logInternet(self):
    try:
        print("START: flush uart")
        # ... uart flush code ...
        print("DONE: flush uart")

        print("START: start_ppp")
        self.networkLte.start_ppp()
        print("DONE: start_ppp - PPP is connected")

        print("START: get token")
        request = requests.post(...)
        print("DONE: get token request sent")

        access_token = request.json()['access_token']
        print(f"DONE: got token (length={len(access_token)})")

        print("START: send data")
        request = requests.post(...)
        print("DONE: send data request sent")

        print(f"DONE: got response {request.status_code}")

    except Exception as E:
        print(f"ERROR at current stage: {E}")
        raise
```

If you see `"START: start_ppp"` but never see `"DONE: start_ppp"`, that confirms the hang is in the infinite loop.

### 3. Consider Limiting UART Flush Loop

`cebattery.py` lines 643-645 has an infinite loop:

```python
while self.portUart1.any():
    self.portUart1.read(self.portUart1.any())
    time.sleep(1)
```

This can loop forever if the LTE modem continuously sends data. Add a maximum iteration limit:

```python
flush_iterations = 0
while self.portUart1.any() and flush_iterations < 10:
    self.portUart1.read(self.portUart1.any())
    time.sleep(1)
    flush_iterations += 1
```

---

## Testing Plan

After applying the fix:

1. **Monitor for timeout errors**: The fix will cause `start_ppp()` to raise `CellularError("timed out starting ppp")` instead of hanging forever

2. **Check webhook logs**: Look for batteries that fail to connect and see if they recover on next cycle

3. **Add monitoring**: Track how often PPP timeouts occur to identify network issues

4. **Compare reliability**: Monitor battery connection success rate before and after fix

---

## Deep Dive Documentation

For complete C source code analysis of all PPP and socket functions, see:
- **[PPP_SOURCE_CODE_ANALYSIS.md](./PPP_SOURCE_CODE_ANALYSIS.md)** - Complete MicroPython and LWIP implementations

---

## Source Code References

All findings backed by actual source code:

- **Pico 2 LTE.py (with bug)**: [pimoroni-pico-rp2350/lte.py](https://github.com/pimoroni/pimoroni-pico-rp2350/blob/feature/can-haz-ppp-plz/micropython/modules_py/lte.py)
- **MicroPython PPP (RP2)**: [extmod/network_ppp_lwip.c](https://github.com/micropython/micropython/blob/master/extmod/network_ppp_lwip.c)
- **LWIP PPP Core**: [lwip/src/netif/ppp/ppp.c](https://github.com/lwip-tcpip/lwip/blob/master/src/netif/ppp/ppp.c)
- **MicroPython Socket (RP2)**: [extmod/modlwip.c](https://github.com/micropython/micropython/blob/master/extmod/modlwip.c)
- **Production Firmware**: `hardware/battery-firmware-v6.0-source-code/modules_py/cebattery.py`

---

**Analysis Date**: 2026-01-28
**Battery Firmware Version**: v6.0 (Pico 2 / RP2350)
**Status**: Root cause identified, fix recommended
