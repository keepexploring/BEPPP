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

**Verified in**:
- [micropython/extmod/network_ppp_lwip.c](https://github.com/micropython/micropython/blob/master/extmod/network_ppp_lwip.c)
- [lwip/src/netif/ppp/ppp.c](https://github.com/lwip-tcpip/lwip/blob/master/src/netif/ppp/ppp.c)

- Only disconnects if in `CONNECTING` or `CONNECTED` state ✅
- Silently returns if called in other states (no crash) ✅
- Handles all PPP phases gracefully ✅
- Safe to call even if `connect()` failed ✅

**Conclusion**: The `stop_ppp()` call in the `finally` block (line 678) is completely safe. Line 678 is NOT the cause of the hang.

---

## 🎯 Root Cause: Infinite Loop in start_ppp()

### The Bug

**File**: [pimoroni-pico-rp2350/lte.py](https://github.com/pimoroni/pimoroni-pico-rp2350/blob/feature/can-haz-ppp-plz/micropython/modules_py/lte.py)

**Location**: `start_ppp()` method

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

### Why This Hangs

PPP `status()` returns values 0-4:
- **4 = Fully connected** (required state)
- 0-3 = Various intermediate states or errors

If PPP fails to reach state 4 (due to network issues, modem errors, incomplete handshake), the firmware **hangs forever** in this while loop.

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

## How the Hang Manifests

### Scenario 1: Hang During Initial Connection

```
1. Battery starts up
2. Calls start_ppp() at cebattery.py line 649
3. PPP connection fails to reach status 4 (network issue, modem error, etc.)
4. start_ppp() HANGS in infinite loop waiting for status 4
5. Firmware never reaches token request (line 658)
6. User sees: "Battery hung, never sent data"
```

### Scenario 2: Hang After Getting Token

```
1. Battery starts up
2. start_ppp() succeeds and PPP connection established
3. Battery successfully gets token (line 659) ✅
4. Tries to send data (line 666)
5. Network conditions change, PPP connection degrades
6. Response never arrives, but socket timeout works so request fails
7. Exception handler calls start_ppp() again (line 654)
8. This time start_ppp() HANGS in infinite loop
9. User sees: "Battery got token but never sent data"
```

This explains the **intermittent** nature of the hang - it depends on network conditions and PPP connection stability.

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
