# Adapter Interface Contract

**TECH-005: Formal specification of adapter requirements, exceptions, threading, and state management**

This document specifies the binding contract that GUI adapters must honor to function correctly with ovos-gui.

---

## Overview

The adapter interface is a **formal contract** with three layers:

1. **Signature Requirements** — Method names, parameter types, return values
2. **Behavioral Requirements** — Threading, exception safety, blocking restrictions
3. **State Management Requirements** — What state adapters can access and modify

Violating any requirement can:
- Crash the ovos-gui service
- Break other adapters
- Cause UI lag or stale state
- Create hard-to-debug race conditions

**Key principle**: Adapters are **trusted code** running in the same process as ovos-gui. They have limited ability to ask questions (via state query API), but **full responsibility** to handle errors gracefully.

---

## Layer 1: Signature Requirements

### Constructor

```python
def __init__(self, config: dict, bus: MessageBusClient | None = None):
    super().__init__(config, bus)
```

| Parameter | Type | Guaranteed |
|-----------|------|-----------|
| `config` | `dict` | Adapter-specific config from `mycroft.conf` → `gui.adapters.<name>`. May be empty. |
| `bus` | `MessageBusClient` or `None` | Shared OVOS MessageBusClient. May be `None` in test contexts. Always use through `self.bus` after initialization. |

**Responsibility**:
- Call `super().__init__(config, bus)` first
- Initialize only lightweight resources (file handles, network sockets, etc. ok; heavy computation not ok)
- Do NOT block the event loop
- Store reference to `self.bus` for later use

---

### Template Handlers (21 methods)

```python
def handle_show_TEXT(self, skill_id: str, data: dict) -> None:
    """Render the TEXT template for a skill.

    Args:
        skill_id: Namespace ID (e.g., "weather.skill")
        data: Session data dict with all keys set by the skill

    Returns:
        None (must not raise exceptions)
    """
```

All 21 handlers:

```
handle_show_idle
handle_show_loading
handle_show_status
handle_show_error
handle_show_text
handle_show_image
handle_show_animated_image
handle_show_list
handle_show_grid
handle_show_table
handle_show_html
handle_show_url
handle_show_audio_player
handle_show_video_player
handle_show_clock
handle_show_timer
handle_show_weather
handle_show_map
handle_show_confirm
handle_show_select
handle_show_face
```

**Parameter Details**:
- `skill_id` (str): The namespace identifier, uniquely identifies the skill showing content
- `data` (dict): The full session data dict for that namespace at call time. Contains all keys set by `gui.value.set` messages. Reserved keys (`__from`, `__idle`, `__animations`) are stripped before this call.

**Responsibility**:
- Implement only the handlers you support (others default to no-op)
- Render the template on your client(s) in a non-blocking way (use threading if needed)
- Return `None`
- Never raise exceptions (catch and log instead)
- Never cache `data` dict — request fresh state via `get_namespace_data()` if needed later

**What NOT to do**:
```python
# ❌ DO NOT cache data from handler signature
self.last_weather_data = data  # <- stale on next update

# ❌ DO NOT block on I/O
response = requests.get(f"http://my-server/data/{skill_id}")  # <- blocks event loop

# ❌ DO NOT raise exceptions
if "temp" not in data:
    raise ValueError(f"Missing temp in weather data")  # <- crashes ovos-gui

# ✅ DO THIS instead
def handle_show_weather(self, skill_id, data):
    if "temp" not in data:
        self.log.warning(f"Weather data missing 'temp' key")
        return

    # Use threading for non-blocking I/O
    thread = Thread(target=self._render_async, args=(skill_id, data))
    thread.daemon = True
    thread.start()
```

---

### Lifecycle Hooks (4 methods)

```python
def on_namespace_activated(self, skill_id: str, site_id: str = "unknown") -> None:
    """Called when a skill's namespace becomes the top of the active stack.

    Args:
        skill_id: Namespace identifier
        site_id: Routing key for client targeting (see ROUTING_KEY_GUIDE.md)

    Returns:
        None (must not raise exceptions)
    """

def on_namespace_deactivated(self, skill_id: str, site_id: str = "unknown") -> None:
    """Called when a skill's namespace is removed from the active stack.

    Args:
        skill_id: Namespace identifier
        site_id: Routing key for client targeting

    Returns:
        None (must not raise exceptions)
    """

def on_idle(self) -> None:
    """Called when GUI returns to idle state (no active skills).

    Returns:
        None (must not raise exceptions)
    """

def on_session_update(self, skill_id: str, data: dict) -> None:
    """Called on every gui.value.set message (data update from skill).

    Args:
        skill_id: Namespace identifier
        data: Only the keys updated in this message (reserved keys stripped)

    Returns:
        None (must not raise exceptions)
    """

def on_status_event(self, event_name: str, data: dict) -> None:
    """Called for system status events forwarded by NamespaceManager.

    Args:
        event_name: Event type (e.g., "recognizer_loop:wakeword")
        data: Event-specific data dict

    Returns:
        None (must not raise exceptions)
    """
```

**Responsibility**:
- Implement only the hooks you care about (others default to no-op)
- Return `None`
- Never raise exceptions
- Callbacks are synchronous — return quickly so other adapters get called

**What NOT to do**:
```python
# ❌ DO NOT assume namespace exists when deactivated
def on_namespace_deactivated(self, skill_id, site_id):
    self.get_namespace_data(skill_id)  # <- may return None if already removed

# ✅ DO THIS instead
def on_namespace_deactivated(self, skill_id, site_id):
    # Clean up your own state; don't query the manager
    self._remove_cached_skill_data(skill_id)
```

---

### State Query Methods (optional, for robustness)

Available on `NamespaceManager` via `self.bus` (see TECH-006 implementation):

```python
def get_active_namespace(self, session_id: str = "default") -> Namespace | None:
    """Get the currently active (top-of-stack) namespace for a session."""

def get_namespace_data(self, namespace_name: str, session_id: str = "default") -> dict | None:
    """Get the full session data dict for a namespace (or None if not loaded)."""

def get_all_sessions(self) -> list[str]:
    """Get list of all active session IDs."""

def is_namespace_active(self, namespace_name: str, session_id: str = "default") -> bool:
    """Check if a namespace is currently active."""
```

**Responsibility**:
- Use these to recover from crashes or missed messages
- Call sparingly (not in tight loops)
- Handle `None` returns gracefully (namespace may be unloaded)

---

## Layer 2: Behavioral Requirements

### Exception Safety (CRITICAL)

**REQUIREMENT**: All adapter methods MUST be exception-safe.

An adapter that raises an exception in a callback will:
1. Stop other adapters from receiving the event
2. Leave ovos-gui in an inconsistent state
3. Require service restart to recover

**Implementation**:

```python
class MyAdapter(AbstractGUIPlugin):
    def handle_show_weather(self, skill_id, data):
        try:
            # Your rendering code here
            temp = data["current_temp"]
            self._render(temp)
        except KeyError as e:
            self.log.error(f"Missing key {e} in weather data")
        except Exception as e:
            self.log.exception(f"Unexpected error in handle_show_weather: {e}")
            # Gracefully degrade; do NOT raise
```

**NamespaceManager will NOT catch adapter exceptions.** Wrapping is done at the call site with `_safe_call()` for robustness, but adapters should not rely on this.

**What NOT to do**:
```python
# ❌ DO NOT assume keys exist
def handle_show_weather(self, skill_id, data):
    temp = data["current_temp"]  # KeyError if missing

# ❌ DO NOT use unvalidated network calls
def handle_show_url(self, skill_id, data):
    requests.get(data["url"])  # May timeout, SSL error, etc.

# ❌ DO NOT assume your GUI client is connected
def handle_show_text(self, skill_id, data):
    self.websocket.send(json.dumps(data))  # Raises if client disconnected
```

---

### Threading Model (CRITICAL)

**REQUIREMENT**: Callbacks are **synchronous** and must not block the ovos-gui event loop.

**How ovos-gui invokes adapters**:

```python
# From NamespaceManager._dispatch_template_to_adapters()
for adapter in self.adapters:
    adapter.dispatch_template(template, skill_id, data)
```

All adapters are called **sequentially, on the main thread**. If Adapter A blocks for 5 seconds, Adapters B and C wait.

**Blocking examples**:
- `requests.get()` — Network call
- `time.sleep()` — Sleep
- Database queries
- Disk I/O (open, read, write)
- Regex on large strings

**Solution: Use threading for blocking operations**:

```python
from threading import Thread

class MyAdapter(AbstractGUIPlugin):
    def handle_show_weather(self, skill_id, data):
        # Return immediately, do work in background
        thread = Thread(target=self._render_async, args=(skill_id, data), daemon=True)
        thread.start()

    def _render_async(self, skill_id, data):
        # Safe to do blocking I/O here
        try:
            response = requests.get("https://api.example.com/weather")
            self._send_to_client(skill_id, response.json())
        except Exception as e:
            self.log.error(f"Background render failed: {e}")
```

**NamespaceManager async callbacks** (future TECH-008):
Currently adapters are called synchronously. Future versions may offer async callback execution via ThreadPoolExecutor per adapter, but do not rely on this yet.

**What NOT to do**:
```python
# ❌ DO NOT block in handlers
def handle_show_weather(self, skill_id, data):
    # This blocks all other adapters for 5 seconds!
    time.sleep(5)
    self._render(data)

# ❌ DO NOT assume your GUI client will respond immediately
def handle_show_text(self, skill_id, data):
    self.websocket.send(data)
    # DO NOT wait for acknowledgement here
    # Use callbacks/async patterns if needed
```

---

### No Long-Running Operations

**REQUIREMENT**: Constructor must complete quickly.

Adapters are loaded at `ovos-gui` startup. A slow adapter blocks the entire service from starting.

**What NOT to do**:
```python
class MyAdapter(AbstractGUIPlugin):
    def __init__(self, config, bus):
        super().__init__(config, bus)

        # ❌ DO NOT wait for external services
        while not self._is_server_ready():
            time.sleep(0.1)

        # ❌ DO NOT download large resources
        self.templates = self._download_from_server()
```

**Solution: Use lazy initialization**:

```python
class MyAdapter(AbstractGUIPlugin):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        self._server_ready = False

        # Start server in background
        Thread(target=self._initialize_async, daemon=True).start()

    def _initialize_async(self):
        # This runs in background; won't block startup
        self._wait_for_server()
        self._server_ready = True
```

---

## Layer 3: State Management Requirements

### What You CAN Access

✅ **Read-only state queries** (when implemented):
- `get_active_namespace()` — current top-of-stack skill
- `get_namespace_data()` — session data for any namespace
- `get_all_sessions()` — all session IDs
- `is_namespace_active()` — quick check

✅ **Configuration**:
- `self.config` — your adapter config dict
- `self.bus` — MessageBusClient for emitting events

✅ **Own private state**:
- Cache keys you set yourself
- WebSocket/network connections you opened
- Render state you maintain

### What You CANNOT Do

❌ **Modify NamespaceManager state directly**:
```python
# DO NOT do this
manager.sessions["default"].active_namespaces.pop()  # <- modifying manager's state
```

❌ **Assume state consistency across callbacks**:
```python
# In on_namespace_activated
ns = self.get_active_namespace()
# Now some time passes... ns may no longer be active!

# In on_namespace_deactivated, NS is already gone
# Don't try to query it — clean up your own state instead
```

❌ **Cache NamespaceManager state long-term**:
```python
# BAD: cache gets stale
def on_namespace_activated(self, skill_id, site_id):
    self.last_active = get_active_namespace()  # <- stale immediately

# GOOD: query fresh when needed
def on_session_update(self, skill_id, data):
    current = self.get_active_namespace()
    if current and current.skill_id == skill_id:
        # Now it's fresh and consistent
```

### Proper State Management Pattern

```python
class ProperAdapter(AbstractGUIPlugin):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        # Store only YOUR data
        self._client_state = {}  # {skill_id: YourState}
        self._sessions = set()

    def on_namespace_activated(self, skill_id, site_id):
        # Create YOUR adapter's state for this skill
        self._client_state[skill_id] = YourState()
        self._sessions.add(site_id)

    def on_namespace_deactivated(self, skill_id, site_id):
        # Clean up YOUR adapter's state
        self._client_state.pop(skill_id, None)
        self._sessions.discard(site_id)

    def on_session_update(self, skill_id, data):
        # Update your representation of skill state
        if skill_id in self._client_state:
            self._client_state[skill_id].update(data)
```

---

## Compliance Checklist

Use this to validate your adapter before release:

- [ ] **Signature Compliance**
  - [ ] Constructor accepts `config` and `bus`
  - [ ] All 21 template handlers exist (may be no-ops)
  - [ ] All lifecycle hooks exist (may be no-ops)
  - [ ] All methods return `None`
  - [ ] All methods accept correct parameters

- [ ] **Exception Safety**
  - [ ] All methods wrap code in try/except
  - [ ] No exceptions escape from adapters
  - [ ] Errors logged with `self.log` (not `print()`)

- [ ] **Threading Safety**
  - [ ] No blocking I/O in synchronous handlers
  - [ ] Blocking code wrapped in `Thread(daemon=True)`
  - [ ] Constructor completes in <100ms
  - [ ] No `time.sleep()` or similar delays

- [ ] **State Management**
  - [ ] No modifications to `NamespaceManager` state
  - [ ] Clean up adapter state on `on_namespace_deactivated`
  - [ ] Gracefully handle missing keys in `data` dicts
  - [ ] No assumptions about state between callbacks

- [ ] **Testing**
  - [ ] Unit tests for each handler with mock data
  - [ ] Integration tests with actual ovos-gui
  - [ ] Tests for error conditions (missing keys, network errors)
  - [ ] Concurrency tests (multiple skills active)

---

## Testing Your Adapter

### Unit Tests (Fast)

```python
import pytest
from my_adapter import MyGUIPlugin

@pytest.fixture
def adapter():
    return MyGUIPlugin({}, bus=None)

def test_handle_show_text_missing_key(adapter):
    """Adapter should not crash on missing keys."""
    data = {"text": "hello"}  # missing 'title'

    # Should not raise
    adapter.handle_show_text("test.skill", data)

def test_handle_show_weather_network_error(adapter):
    """Adapter should handle network failures."""
    data = {"current_temp": 22, "condition": "sunny"}

    # Mock network error
    with patch.object(adapter, '_send_to_client', side_effect=NetworkError):
        # Should not raise
        adapter.handle_show_weather("test.skill", data)
```

### Integration Tests (with ovos-gui)

```python
from ovos_utils.fakebus import FakeBus
from ovos_gui.namespace import NamespaceManager
from my_adapter import MyGUIPlugin

def test_adapter_with_ovos_gui():
    """Test adapter in full ovos-gui context."""
    bus = FakeBus()
    manager = NamespaceManager(bus)
    adapter = MyGUIPlugin({}, bus=bus)
    manager.adapters.append(adapter)

    # Simulate skill showing content
    from ovos_bus_client.message import Message
    msg = Message("gui.page.show", data={
        "page_names": ["SYSTEM_weather"],
        "__from": "weather.skill",
        "current_temp": 22
    }, context={"session": {"session_id": "default", "site_id": "default"}})

    manager.handle_show_page(msg)

    # Verify adapter was called
    assert adapter was called for weather
```

---

## Validating Adapter Compliance in CI

Add this to your adapter's `.github/workflows/test.yml`:

```yaml
- name: Check adapter interface compliance
  run: |
    python -m pytest tests/ -v \
      --tb=short \
      -k "test_exception_safety or test_threading or test_state_management"
```

---

## Related Documentation

- **[adapter-plugins.md](adapter-plugins.md)** — Plugin registration and configuration
- **[ROUTING_KEY_GUIDE.md](../ROUTING_KEY_GUIDE.md)** — `site_id` semantics for client targeting
- **[bus-protocol.md](bus-protocol.md)** — MessageBus message formats
- **[Source: AbstractGUIPlugin](../../ovos_gui/namespace.py)** — Interface definition
- **[Source: NamespaceManager._safe_call](../../ovos_gui/namespace.py)** — How exceptions are wrapped

---

## Common Adapter Patterns

### Web-Based Adapter (WebSocket to browser)

```python
class WebGUIAdapter(AbstractGUIPlugin):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        self.port = config.get("port", 8080)
        self._clients = {}  # {site_id: [websocket_connections]}

        # Start server in background (don't block)
        Thread(target=self._start_server, daemon=True).start()

    def handle_show_weather(self, skill_id, data):
        # Send to all connected clients (non-blocking)
        Thread(target=self._send_to_clients, args=("weather", data), daemon=True).start()

    def _send_to_clients(self, template, data):
        try:
            payload = json.dumps({"template": template, "data": data})
            for conn in self._clients.values():
                conn.send(payload)
        except Exception as e:
            self.log.error(f"Failed to send to clients: {e}")
```

### Terminal-Based Adapter

```python
class TerminalGUIAdapter(AbstractGUIPlugin):
    def handle_show_text(self, skill_id, data):
        try:
            print(f"\n[{skill_id}]")
            print(f"Title: {data.get('title', 'N/A')}")
            print(f"Text: {data.get('text', 'N/A')}\n")
        except Exception as e:
            self.log.error(f"Display error: {e}")

    def on_namespace_deactivated(self, skill_id, site_id):
        print(f"[{skill_id}] closed\n")
```

### Legacy Qt Adapter (Reference)

See: `docs/adapter-development/legacy-qt-plugin.md` for the canonical reference implementation.

---

## Version Compatibility

This contract applies to:
- **ovos-gui** >= 0.1.3
- **ovos-plugin-manager** >= 0.5.5
- **Python** >= 3.10

---

**Last Updated**: 2026-03-12
**Status**: Formal specification for TECH-005
**Audience**: GUI adapter developers, ovos-gui maintainers
