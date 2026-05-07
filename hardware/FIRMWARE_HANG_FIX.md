# Battery Firmware Hang Analysis & Fixes

## Problem Statement
Battery firmware occasionally hangs after successfully receiving authentication token but before sending data. Analysis shows three critical hang points.

---

## Issue #1: Socket Timeout May Not Work (CRITICAL)

### Location
- `cebattery.py` line 658: `requests.post(..., timeout=20)`
- `cebattery.py` line 666: `requests.post(..., timeout=20)`

### Root Cause
In `requests/__init__.py` lines 90-93:
```python
if timeout is not None:
    # Note: settimeout is not supported on all platforms, will raise
    # an AttributeError if not available.
    s.settimeout(timeout)
```

**The timeout parameter might not work on Pico 2!** If `socket.settimeout()` is not implemented or fails silently, the following operations can hang indefinitely:
- Line 96: `s.connect()` - Socket connection
- Line 148: `s.readline()` - Reading HTTP response
- Line 159: `s.readline()` - Reading HTTP headers (in loop)

### Why This Causes Intermittent Hangs
- The hang is intermittent because network conditions vary
- Sometimes the server responds quickly (no hang)
- Sometimes there's network latency, partial responses, or SSL issues (hang)
- Without a working timeout, there's no way to recover

### Fix Option A: Verify Socket Timeout Support
Add debugging to check if `settimeout()` works:

```python
# In cebattery.py, before first requests call:
import socket
test_socket = socket.socket()
try:
    test_socket.settimeout(5)
    print("Socket timeout SUPPORTED")
except AttributeError:
    print("Socket timeout NOT SUPPORTED - WILL HANG!")
test_socket.close()
```

### Fix Option B: Use select() for Timeout (Workaround)
If `settimeout()` doesn't work, use `select.select()` with timeout instead:

```python
import select

# In requests/__init__.py, replace line 90-93:
if timeout is not None:
    try:
        s.settimeout(timeout)
    except (AttributeError, NotImplementedError):
        # Fallback: Use select() for timeout
        # This requires wrapping socket operations in select checks
        pass
```

### Fix Option C: External Watchdog Timer (Safest)
Use MicroPython's watchdog timer to force reset if firmware hangs:

```python
from machine import WDT

# In cebattery.py, early in the script:
wdt = WDT(timeout=120000)  # 2 minute watchdog

# Feed watchdog regularly throughout execution:
wdt.feed()  # Before each major operation
```



---

## Issue #2: JSON Decoding Hangs on Incomplete Response

### Location
`cebattery.py` line 659: `access_token = request.json()['access_token']`

### Root Cause
The `.json()` method calls `.content` which calls `self.raw.read()`:

```python
# requests/__init__.py line 18-24
@property
def content(self):
    if self._cached is None:
        try:
            self._cached = self.raw.read()  # ← Can hang here
        finally:
            self.raw.close()
            self.raw = None
    return self._cached
```

If the socket has no working timeout and the server:
- Sends HTTP headers but hangs before sending body
- Has SSL handshake issues
- Closes connection unexpectedly

Then `self.raw.read()` will hang waiting for data that never comes.

### Fix: Add Explicit Error Handling

```python
# In cebattery.py, replace line 658-659:
try:
    request = requests.post('https://api.beppp.cloud/auth/battery-login',
                            json={'battery_id': BATTERY_ID, 'battery_secret': BATTERY_KEY},
                            timeout=20)

    # Check status code before decoding JSON
    if request.status_code != 200:
        print(f"ERROR: Login failed with status {request.status_code}")
        raise Exception(f"HTTP {request.status_code}")

    # Try to decode JSON with error handling
    try:
        response_data = request.json()
    except Exception as json_error:
        print(f"ERROR: Failed to decode JSON response: {json_error}")
        raise

    # Check if access_token exists in response
    if 'access_token' not in response_data:
        print(f"ERROR: No access_token in response: {response_data}")
        raise Exception("Missing access_token")

    access_token = response_data['access_token']
    print("success, access token:", access_token)

except Exception as E:
    print(f"ERROR: Token request failed: {E}")
    self.lteError = True
    raise
```

---

## Issue #3: `stop_ppp()` Crashes if `start_ppp()` Failed

### Location
`cebattery.py` lines 651-654 and 678

### Root Cause Sequence

1. **Line 649**: `self.networkLte.start_ppp()` - Attempts to start PPP
2. **If it fails**, line 653: `self.networkLte.stop_ppp()` - Tries to stop PPP
3. **Line 678** (finally block): `self.networkLte.stop_ppp()` - Always tries to stop

**The problem**: `stop_ppp()` in `lte.py` line 82 calls `self._ppp.disconnect()` without checking if `self._ppp` exists!

```python
# lte.py line 81-89
def stop_ppp(self):
    self._ppp.disconnect()  # ← AttributeError if self._ppp doesn't exist
    self._send_at_command(f"AT+IPR={DEFAULT_UART_STARTUP_BAUD}")
    self._flush_uart()
    self._uart.init(...)
```

If `start_ppp()` failed before line 113 (`self._ppp = PPP(self._uart)`), then `self._ppp` was never created, causing `stop_ppp()` to crash.

### When This Happens
`start_ppp()` can fail at multiple points before creating `self._ppp`:
- Line 92: `self._wait_ready()` times out
- Line 95: `self._send_at_command()` fails
- Line 106: `self.connect()` fails
- Line 110-111: AT command fails

### Fix Option A: Make `stop_ppp()` Safe

```python
# In lte.py, replace stop_ppp() method:
def stop_ppp(self):
    # Check if PPP was ever initialized before trying to disconnect
    if hasattr(self, '_ppp') and self._ppp is not None:
        try:
            self._ppp.disconnect()
        except Exception as e:
            print(f"Warning: PPP disconnect failed: {e}")

    # Continue with cleanup regardless
    try:
        self._send_at_command(f"AT+IPR={DEFAULT_UART_STARTUP_BAUD}")
        self._flush_uart()
        self._uart.init(
            baudrate=DEFAULT_UART_STARTUP_BAUD,
            timeout=DEFAULT_UART_TIMEOUT,
            timeout_char=DEFAULT_UART_TIMEOUT_CHAR,
            rxbuf=DEFAULT_UART_RXBUF)
    except Exception as e:
        print(f"Warning: UART cleanup failed: {e}")
```

### Fix Option B: Track PPP State in cebattery.py

```python
# In cebattery.py, replace lines 648-678:
ppp_started = False
try:
    print("flush uart input")
    self.portUart1.flush()
    time.sleep(1)
    while self.portUart1.any():
        self.portUart1.read(self.portUart1.any())
        time.sleep(1)

    # start LTE link
    print("start LTE ppp network")
    try:
        self.networkLte.start_ppp()
        ppp_started = True  # Only set to True if start_ppp() succeeded
    except Exception as E:
        # if it failed, give it one more try
        print("start ppp failed, try one more time")
        # Only call stop_ppp() if we successfully started
        if ppp_started:
            self.networkLte.stop_ppp()
        self.networkLte.start_ppp()
        ppp_started = True

    # ... rest of code ...

except Exception as E:
    print("error")
    self.lteError = True
    if RAISE_EXCEPTIONS:
        raise
finally:
    try:
        print("stop LTE ppp network")
        # Only stop if we successfully started
        if ppp_started:
            self.networkLte.stop_ppp()
        print("success")
    except Exception as E:
        print("error")
        self.lteError = True
```

---

## Additional Findings

### Infinite UART Flush Loop (Already Identified)
`cebattery.py` lines 643-645:
```python
while self.portUart1.any():
    self.portUart1.read(self.portUart1.any())
    time.sleep(1)
```

This can loop forever if the LTE modem continuously sends data. Should have maximum iteration limit.

---

## Recommended Implementation Priority

1. **CRITICAL - Add Watchdog Timer** (Fix Option C for Issue #1)
   - Easiest to implement
   - Provides automatic recovery from ANY hang
   - Already implemented in `cebattery_improved.py`

2. **HIGH - Fix `stop_ppp()` Safety** (Fix Option A for Issue #3)
   - Prevents crash in error recovery path
   - Low risk change

3. **HIGH - Add PPP State Tracking** (Fix Option B for Issue #3)
   - More robust than just fixing `stop_ppp()`
   - Prevents calling cleanup on uninitialized resources

4. **MEDIUM - Add JSON Error Handling** (Fix for Issue #2)
   - Better error messages
   - Prevents mysterious hangs on malformed responses

5. **LOW - Test Socket Timeout** (Fix Option A for Issue #1)
   - Diagnostic only
   - Helps understand if timeout works on Pico 2

6. **LOW - Limit UART Flush Iterations**
   - Already identified in original analysis
   - Low probability of occurrence

---

## How to Check if Socket Timeout Works on Pico 2

The critical question is: **Does `socket.settimeout()` actually work on MicroPython for Pico 2?**

### Test Script

Upload this to the battery and run it:

```python
import socket
import time

print("Testing socket timeout support...")

# Test 1: Check if method exists
s = socket.socket()
if not hasattr(s, 'settimeout'):
    print("FAIL: socket.settimeout() method does not exist!")
    s.close()
else:
    print("PASS: socket.settimeout() method exists")

    # Test 2: Check if it can be called without error
    try:
        s.settimeout(5)
        print("PASS: socket.settimeout(5) called successfully")
    except Exception as e:
        print(f"FAIL: socket.settimeout(5) raised exception: {e}")
        s.close()

    # Test 3: Check if timeout actually works
    print("Testing if timeout actually works (connecting to non-routable IP)...")
    s.close()
    s = socket.socket()
    s.settimeout(3)

    start = time.time()
    try:
        # Try to connect to a non-routable IP (should timeout after 3 seconds)
        s.connect(('10.255.255.1', 80))
        print("FAIL: Connection succeeded (shouldn't happen)")
    except OSError as e:
        elapsed = time.time() - start
        print(f"Got OSError after {elapsed:.1f} seconds: {e}")
        if 2 < elapsed < 4:
            print("PASS: Timeout worked correctly (took ~3 seconds)")
        else:
            print(f"FAIL: Timeout did not work (took {elapsed:.1f}s, expected ~3s)")
    except Exception as e:
        elapsed = time.time() - start
        print(f"Got other exception after {elapsed:.1f} seconds: {e}")
    finally:
        s.close()

print("Test complete")
```

**Expected results:**
- **If timeout works**: Test should complete in ~3 seconds with "PASS: Timeout worked correctly"
- **If timeout doesn't work**: Test will hang at `s.connect()` indefinitely

---

## Searching for PPP and Socket Source Code

As you mentioned, `PPP` and `socket` are likely implemented in C. Here's where to find them:

### MicroPython Socket Implementation
Source: https://github.com/micropython/micropython

Key files:
- `extmod/modusocket.c` - Socket module implementation
- `extmod/modussl_mbedtls.c` - SSL/TLS implementation
- Look for `mp_obj_socket_settimeout` function

### PPP Implementation
Source: https://github.com/pimoroni/micropython (Pimoroni fork)

Key files:
- `extmod/network_ppp.c` - PPP network implementation
- Look for `ppp_connect()` and `ppp_disconnect()` functions

### How to Search
```bash
# Clone the Pimoroni MicroPython repo
git clone https://github.com/pimoroni/micropython.git
cd micropython

# Search for socket timeout implementation
grep -r "settimeout" extmod/

# Search for PPP implementation
grep -r "class.*PPP\|ppp_connect\|ppp_disconnect" extmod/ ports/
```

---

## Conclusion

The most likely cause of the hang is **socket timeout not working properly on Pico 2**. The `requests` library assumes `socket.settimeout()` works, but the comment in the code suggests it may not be supported on all platforms.

**Immediate recommendation**: Add a watchdog timer as the first line of defense. This is already implemented in `cebattery_improved.py` but missing from the production `cebattery.py`.

**Long-term recommendation**: Test whether socket timeout actually works on Pico 2, and if not, implement a workaround using `select()` or periodic watchdog feeds during socket operations.
