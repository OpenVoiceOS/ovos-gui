# Debugging Guide: ovos-gui

**How to debug and troubleshoot the ovos-gui MessageBus service**

---

## Debugging Modes

### Enable Debug Logging

ovos-gui uses Python's standard logging. Enable debug output:

```bash
# Run ovos-gui with debug logging
python3 -m ovos_gui --log-level debug

# Or set environment variable
export OVOS_LOG_LEVEL=debug
python3 -m ovos_gui
```

### Debug Output Shows

- ✅ MessageBus connections
- ✅ Incoming event messages
- ✅ Session data changes
- ✅ Adapter plugin loading
- ✅ User interactions
- ✅ Error traces

---

## Command-Line Debugging

### View Live Logs

```bash
# Run with verbose output
python3 -m ovos_gui -vv

# Or using logging
export OVOS_LOG_LEVEL=debug
python3 -m ovos_gui
```

### Print Debugging (logging module)

Add temporary debug output in your code:

```python
# ovos_gui/manager.py
import logging
log = logging.getLogger(__name__)

class GUIManager:
    def _handle_page_show(self, message):
        log.debug(f"Page show: namespace={message.data.get('namespace')}")
        log.debug(f"Session data: {message.data.get('sessionData')}")

        # Your actual code
        self.sessions[namespace] = message.data
```

Run with logging enabled:
```bash
export OVOS_LOG_LEVEL=debug
python3 -m ovos_gui
```

---

## IDE Debugging

### PyCharm IDE

1. **Set breakpoints**: Click in line number margin (red dot)
2. **Debug mode**: Right-click `__main__.py` → Debug
3. **Execution stops**: At breakpoint, inspect variables
4. **Step controls**:
   - F10 (Step over)
   - F11 (Step into)
   - Shift+F11 (Step out)
   - F9 (Resume)

### VS Code with Python Extension

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug ovos-gui",
            "type": "python",
            "request": "launch",
            "module": "ovos_gui",
            "console": "integratedTerminal",
            "env": {"OVOS_LOG_LEVEL": "debug"}
        }
    ]
}
```

Run with F5 (Start Debugging).

---

## Logging Best Practices

### For Users (Production)

Minimal logging:
```python
import logging
log = logging.getLogger(__name__)

# Only log critical errors
log.error(f"Failed to load adapter: {error}")
```

### For Developers (Development)

Detailed logging:
```python
import logging
log = logging.getLogger(__name__)

log.debug(f"Initializing GUIManager")
log.debug(f"  MessageBus host: {self.messagebus.host}")
log.debug(f"  Base port: {self.base_port}")
log.debug(f"Session created: {namespace}")
log.debug(f"  Template: {template}")
log.debug(f"  Data keys: {list(data.keys())}")
```

### Conditional Logging

```python
import os
import logging

DEBUG = os.environ.get("DEBUG_OVOS_GUI", "false").lower() == "true"

if DEBUG:
    log.debug("Detailed debug information")
```

Enable with:
```bash
DEBUG_OVOS_GUI=true python3 -m ovos_gui
```

---

## Debugging MessageBus Events

### Monitor All Events

Create a test script to capture events:

```python
# test_event_monitor.py
from ovos_bus_client import MessageBusClient
import json

bus = MessageBusClient()

def on_any_event(message):
    print(f"\n{'='*60}")
    print(f"Event: {message.msg_type}")
    print(f"Data: {json.dumps(message.data, indent=2)}")
    print(f"{'='*60}")

# Listen to all gui.* events
bus.on("gui.#", on_any_event)

# Keep running
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Monitoring stopped")
```

Run in another terminal:
```bash
python3 test_event_monitor.py
```

Then trigger events in your skill or GUI and see them appear.

### Inspect Specific Event

```python
# test_inspect_event.py
from ovos_bus_client import MessageBusClient
import json

bus = MessageBusClient()

def on_page_show(message):
    print(f"gui.page.show received:")
    print(f"  namespace: {message.data.get('namespace')}")
    print(f"  template: {message.data.get('template')}")
    print(f"  sessionId: {message.data.get('sessionId')}")
    data = message.data.get('sessionData', {})
    print(f"  session data keys: {list(data.keys())}")
    print(f"  full data: {json.dumps(data, indent=4)}")

bus.on("gui.page.show", on_page_show)

print("Listening for gui.page.show events...")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Stopped")
```

---

## GDB Command-Line Debugging (Advanced)

For shell-based debugging on remote servers:

```bash
# Start ovos-gui under Python debugger
python3 -m pdb -m ovos_gui

# Or with breakpoint
python3 -c "
import pdb; pdb.set_trace()
from ovos_gui import GUIManager
# (continue execution with 'c')
"
```

**Common pdb commands:**
```
l (list)      - Show source code
b (break)     - Set breakpoint
c (continue)  - Resume
s (step)      - Step into
n (next)      - Next line
p <var>       - Print variable
h (help)      - Show help
```

---

## Debugging Adapters

### Test Adapter Loading

```python
# test_adapter_loading.py
from ovos_plugin_manager.templates.gui import GuiAdapterModel

print("Available GUI adapters:")
adapters = GuiAdapterModel.get_all_plugins()

for adapter_name, adapter_class in adapters.items():
    print(f"\n  {adapter_name}:")
    print(f"    Class: {adapter_class}")
    print(f"    Module: {adapter_class.__module__}")

    # Try to instantiate
    try:
        instance = adapter_class()
        print(f"    ✓ Loaded successfully")
        print(f"    Methods: {dir(instance)}")
    except Exception as e:
        print(f"    ✗ Failed to load: {e}")
```

Run:
```bash
python3 test_adapter_loading.py
```

### Mock Adapter Messages

Test how adapters receive events:

```python
# test_adapter_integration.py
from ovos_bus_client import MessageBusClient
from unittest.mock import MagicMock

# Create mock adapter
class MockAdapter:
    def __init__(self):
        self.events_received = []

    def on_page_show(self, message):
        self.events_received.append(message)
        print(f"Adapter received: {message.data}")

# Create bus and adapter
bus = MessageBusClient()
adapter = MockAdapter()

# Simulate GUI sending event
from ovos_utils.messagebus import Message

message = Message(
    "gui.page.show",
    {
        "namespace": "skill-test",
        "template": "SYSTEM_weather",
        "sessionData": {"temp": 22}
    }
)

adapter.on_page_show(message)
print(f"Total events: {len(adapter.events_received)}")
```

---

## Memory Debugging

### Monitor Memory Usage

```bash
# While running ovos-gui
watch -n 1 'ps aux | grep ovos-gui'

# Or with more details
python3 -c "
import psutil
import time

proc = psutil.Process()
while True:
    mem = proc.memory_info()
    print(f'RSS: {mem.rss / 1024 / 1024:.1f} MB')
    time.sleep(1)
"
```

### Check for Memory Leaks

```bash
# Install memory_profiler
pip install memory-profiler

# Run with profiling
python3 -m memory_profiler -m ovos_gui
```

---

## Network Debugging

### Monitor MessageBus Traffic

```bash
# Install tcpdump
sudo tcpdump -i lo -A 'tcp port 8081'

# Or use netstat to see connections
netstat -tlnp | grep python3
```

### Check WebSocket Connections

```python
# test_websocket_monitor.py
import socket
import time

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

base_port = 18181
for i in range(5):
    port = base_port + i
    if check_port(port):
        print(f"✓ Port {port}: GUI adapter connected")
    else:
        print(f"✗ Port {port}: No adapter")
```

---

## Common Issues & Debugging

### Issue: "MessageBus connection refused"

**Diagnosis:**
```bash
# Check if ovos-gui is running
ps aux | grep ovos-gui

# Check if MessageBus is running
ps aux | grep message

# Try connecting manually
python3 -c "from ovos_bus_client import MessageBusClient; bus = MessageBusClient(); print('Connected')"
```

**Solution:**
- Start ovos-core first (which starts MessageBus)
- Check port 8181 is accessible
- Check firewall isn't blocking port

### Issue: "Adapter failed to load"

**Diagnosis:**
```python
# Run adapter loading test
python3 test_adapter_loading.py

# Or in Python directly
from ovos_plugin_manager.templates.gui import GuiAdapterModel
adapters = GuiAdapterModel.get_all_plugins()
print(adapters)
```

**Solution:**
- Check adapter package is installed: `pip list | grep gui-adapter`
- Check entry point in adapter's `setup.py`
- Run with debug logging to see error

### Issue: "Session data not persisting"

**Diagnosis:**
```python
# Add debug logging to session handling
import logging
logging.basicConfig(level=logging.DEBUG)

from ovos_gui.manager import GUIManager

gui = GUIManager(messagebus)

# Add breakpoint to inspect
import pdb; pdb.set_trace()
# ... trigger event ...
# >>> gui.sessions
```

**Solution:**
- Check session namespace spelling
- Verify message data format
- Check adapter is receiving events

### Issue: "User interaction not reaching skill"

**Diagnosis:**
```python
# Monitor events
python3 test_event_monitor.py

# Look for gui.user.interaction events
# Check if they route to skill
```

**Solution:**
- Check namespace matches skill name
- Verify action field is correct
- Check bus connection to skill

---

## Debugging Checklist

Before asking for help:

- [ ] Run with `--log-level debug`
- [ ] Check recent logs in `~/.cache/`
- [ ] Verify MessageBus is running
- [ ] Verify all adapters are loaded
- [ ] Check firewall rules
- [ ] Monitor MessageBus events with test script
- [ ] Review [bus-protocol.md](../adapter-development/bus-protocol.md) for message format
- [ ] Test with mock components
- [ ] Check error in stack trace

---

## Advanced Debugging Tools

### Use pdbpp (Better Debugger)

```bash
pip install pdbpp

# Use automatically
python3 -m ovos_gui --debugger
```

### Use ipdb (IPython Debugger)

```bash
pip install ipdb

# Add to code
import ipdb; ipdb.set_trace()
```

### Use Python's Traceback

```python
import traceback

try:
    gui.handle_message(message)
except Exception as e:
    traceback.print_exc()
    log.error(f"Failed: {e}")
```

---

## Logging Configuration

### Custom Logging Setup

```python
# Set up logging in your test
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger('ovos_gui')
```

---

## Next Steps

- Read [contributing.md](contributing.md) — Contribution guidelines
- Check [TESTING.md](TESTING.md) — How to test changes
- Review [adapter-development/bus-protocol.md](../adapter-development/bus-protocol.md) — Protocol reference

---

**Happy debugging!** 🐛
