# State Management Audit: ovos-gui Architecture

**Date**: 2026-03-12
**Scope**: Complete analysis of namespace, session, and active skill state management
**Status**: ✅ Fully documented and integrated with adapter plugins

---

## Executive Summary

The ovos-gui state management system implements a **LIFO stack-based namespace manager** that coordinates between the OVOS MessageBus and GUI adapter plugins. The system tracks:

1. **Active Skills Stack** — namespace display priority (skill at index 0 is visible)
2. **Namespace Data** — key/value session data per skill
3. **Page Management** — which QML pages/templates are active per namespace
4. **Persistence** — automatic timeout and removal of non-persistent skills
5. **Message Forwarding** — 41 system events (eyes, mouth, audio, recognition) to GUI clients

The namespace manager is **NOT an entry point plugin** — it's a core component instantiated by `GUIService` and notifies adapters via callbacks, not bus messages.

---

## Architecture Overview

```
GUIService (ovos_gui/service.py)
    │
    ├─ MessageBusClient (port 8181 — internal)
    │   │
    │   ├─ Listens for skill GUI requests (gui.page.show, gui.value.set, etc.)
    │   ├─ Listens for 41 system events (enclosure, audio, recognition)
    │   └─ Listens for GUI interactions (page_gained_focus, page_interaction)
    │
    └─ NamespaceManager (ovos_gui/namespace.py)
        │
        ├─ Manages active_namespaces LIFO stack
        ├─ Manages loaded_namespaces dict (cache)
        ├─ Manages session data per namespace
        ├─ Manages page lifecycle and persistence
        │
        └─ GUI Adapter Plugins (multiple)
            │
            ├─ on_namespace_activated(skill_id, site_id)
            ├─ on_namespace_deactivated(skill_id)
            ├─ on_session_update(skill_id, data, site_id)
            ├─ on_status_event(msg_type, data, site_id)
            ├─ dispatch_template(template, skill_id, data, site_id)
            └─ any_client_connected() — used for status checks
```

**Key Point**: Adapters are **NOT entry points**. They're instantiated and managed by GUIService, which passes them to NamespaceManager for callbacks.

---

## Component Breakdown

### 1. GUIService (service.py)

**Responsibilities**:
- Create and connect to the OVOS MessageBus
- Load GUI adapter plugins (`opm.gui_adapter`)
- Instantiate NamespaceManager with adapters
- Manage service lifecycle (alive, ready, stopping)

**Code Path**: `service.py:68-80`

```python
def run(self):
    self.status.set_alive()
    self._init_bus_client()
    self.pip_installer = ServiceInstaller(self.bus, service_name="ovos_gui")
    adapters = self._load_adapter_plugins()  # Load from opm.gui_adapter entry point
    self.namespace_manager = NamespaceManager(self.bus, adapters=adapters)
    self.status.set_ready()
```

**Adapter Loading**: `service.py:56-66`
```python
def _load_adapter_plugins(self):
    from ovos_plugin_manager.gui_adapter import OVOSGUIAdapterFactory
    adapter_config = Configuration().get("gui", {}).get("adapters", {})
    adapters = OVOSGUIAdapterFactory.create_all(config=adapter_config, bus=self.bus)
    return adapters
```

---

### 2. NamespaceManager (namespace.py)

**Core State**:
- `active_namespaces: List[Namespace]` — LIFO stack (index 0 = visible)
- `loaded_namespaces: Dict[str, Namespace]` — cache of all namespaces
- `remove_namespace_timers: Dict[str, Timer]` — auto-removal timers
- `adapters: List` — GUI adapter plugins

**Message Handlers** (lines 403-417):

| Message Type | Handler | Purpose |
|---|---|---|
| `gui.clear.namespace` | `handle_clear_namespace()` | Skill requests namespace removal |
| `gui.event.send` | `handle_send_event()` | Skill sends custom event to GUI |
| `gui.page.delete` | `handle_delete_page()` | Remove specific pages |
| `gui.page.delete.all` | `handle_delete_all_pages()` | Remove all pages (except specified) |
| `gui.page.show` | `handle_show_page()` | Show pages + activate namespace |
| `gui.status.request` | `handle_status_request()` | Check if any client connected |
| `gui.value.set` | `handle_set_value()` | Update namespace session data |
| `gui.page_interaction` | `handle_page_interaction()` | User swiped/clicked page |
| `gui.page_gained_focus` | `handle_page_gained_focus()` | Page gained focus event |
| `mycroft.gui.screen.close` | `handle_namespace_global_back()` | Global back button pressed |

**System Event Forwarding** (lines 419-471):
All 41 messages are converted to `mycroft.events.triggered` and forwarded to adapters:
- `forward_to_gui()` → calls adapter's `on_status_event()` callback
- Messages include enclosure eyes, mouth, audio, recognition state

---

### 3. Namespace (namespace.py:79-380)

**Per-Namespace State**:
- `skill_id` — namespace identifier (usually skill_id)
- `persistent: bool` — True = indefinite, False = timed removal
- `duration: int` — seconds before auto-removal (0 if persistent)
- `pages: List[GuiPage]` — active pages in this namespace
- `data: Dict` — session key/value pairs
- `page_number: int` — currently displayed page index

**Lifecycle Methods**:

| Method | Purpose | Output Message |
|---|---|---|
| `add()` | Add namespace to active stack | `mycroft.session.list.insert` (top of stack) |
| `activate(position)` | Move existing namespace to top | `mycroft.session.list.move` (from position → 0) |
| `remove(position)` | Remove from active stack | `mycroft.session.list.remove` + cleanup data |
| `load_data(key, value)` | Update session data | `mycroft.session.set` |
| `unload_data(key)` | Delete session data | `mycroft.session.delete` |
| `load_pages(pages, show_index)` | Load new pages | `mycroft.gui.list.insert` |
| `remove_pages(positions)` | Delete pages | `mycroft.gui.list.remove` |
| `focus_page(page)` / `_activate_page(page)` | Focus specific page | `mycroft.events.triggered` (page_gained_focus) |

**Note**: `send_message_to_gui()` is currently a **TODO** placeholder (line 108) — adapters handle messaging.

---

### 4. GuiPage (page.py)

Simple dataclass representing a single display page:

```python
@dataclass
class GuiPage:
    name: str                          # Page identifier
    persistent: bool                   # Keep until removed?
    duration: Union[int, bool]         # Seconds if not persistent
    namespace: Optional[str] = None    # Parent skill_id
```

---

## State Flows

### Flow 1: Skill Requests to Show a Page

```
Skill → gui.page.show (MessageBus)
    │
    └─ NamespaceManager.handle_show_page()
        │
        ├─ Parse persistence: _parse_persistence()
        │   └─ Result: (persistent: bool, duration: int)
        │
        ├─ If SYSTEM_* template:
        │   └─ _dispatch_template_to_adapters()
        │       └─ Call adapter.dispatch_template() for each adapter
        │
        ├─ Ensure namespace exists: _ensure_namespace_exists()
        │   └─ Create if needed, add to loaded_namespaces
        │
        ├─ Activate namespace: _activate_namespace()
        │   │
        │   ├─ If already in active_namespaces: move to top (activate)
        │   ├─ Else: add to top of active_namespaces
        │   │
        │   └─ Notify adapters:
        │       ├─ adapter.on_namespace_activated(skill_id, site_id)
        │       └─ Sync initial data: namespace.load_data() for each key
        │
        ├─ Load pages: _load_pages()
        │   └─ namespace.load_pages(pages, show_index)
        │       └─ namespace._add_pages() / namespace._activate_page()
        │
        └─ Update persistence: _update_namespace_persistence()
            │
            ├─ Remove lower-priority non-persistent namespaces
            ├─ Set persistence on active namespace
            │
            └─ If not persistent:
                └─ _schedule_namespace_removal()
                    └─ Timer fires after duration seconds
                        └─ _remove_namespace_via_timer()
```

**Output Messages** (from Namespace → adapters):
- `mycroft.session.list.insert` — namespace added to active stack
- `mycroft.gui.list.insert` — pages inserted
- `mycroft.events.triggered` (page_gained_focus) — page focus changed

**Adapter Callbacks**:
- `dispatch_template()` — for SYSTEM_* templates
- `on_namespace_activated()` — namespace became visible
- `on_session_update()` — initial/updated data

---

### Flow 2: User Interacts with Page

```
User → GUI Client (via adapter) → gui.page_interaction (MessageBus)
    │
    └─ NamespaceManager.handle_page_interaction()
        │
        ├─ Get namespace and page_number from message
        ├─ If page changed: namespace.page_gained_focus(new_page_number)
        │
        └─ If namespace not persistent:
            └─ Reschedule removal timer (restart duration countdown)
```

**Effect**: User interaction resets the auto-removal timer, keeping the skill visible longer.

---

### Flow 3: Skill Sends Custom Event

```
Skill → gui.event.send (MessageBus)
    │
    └─ NamespaceManager.handle_send_event()
        │
        └─ Create mycroft.events.triggered message
            └─ Notify adapters (TODO: how are custom events sent to clients?)
```

**Status**: ⚠️ **Unclear** — adapters are notified, but the mechanism for delivering custom events to GUI clients needs clarification.

---

### Flow 4: System Event Forwarding

```
System Service → Message X (MessageBus)
    │
    └─ NamespaceManager.forward_to_gui()
        │
        ├─ Transform: Message → mycroft.events.triggered
        │   ├─ namespace = "system"
        │   ├─ event_name = message.msg_type
        │   └─ data = message.data
        │
        └─ Notify adapters:
            └─ adapter.on_status_event(msg_type, data, site_id)
```

**Examples**: enclosure.eyes.on, speak, recognizer_loop:wakeword, etc. (41 total)

---

## Session Management

### Session Data State

Each namespace maintains a `data: Dict` of key-value pairs:

```python
# Namespace.data = { "temp": 25, "location": "Berlin", "condition": "cloudy" }
# These are synced to GUI clients via mycroft.session.set messages
```

**Update Path**:
```
Skill → gui.value.set (MessageBus)
    │
    └─ NamespaceManager.handle_set_value()
        │
        ├─ _update_namespace_data(namespace_name, data)
        │   └─ Update namespace.data dict
        │
        └─ If namespace is active:
            ├─ namespace.load_data(key, value) for each changed key
            └─ Notify adapters: adapter.on_session_update(skill_id, data, site_id)
```

**Reserved Keys**:
- `__from` — source namespace (OVOS internal, filtered out before sending to adapters)
- `__idle` — persistence flag (OVOS internal, filtered out before sending to adapters)

---

## Active Namespaces Stack (LIFO)

**Invariant**: `active_namespaces[0]` is always the visible namespace.

**Stack Operations**:

| Operation | When | Handler |
|---|---|---|
| **Insert at 0** | New skill activated | `_activate_namespace()` → namespace.add() |
| **Move to 0** | Existing skill re-activated | `_activate_namespace()` → namespace.activate(position) |
| **Remove** | Skill times out or explicitly removed | `_remove_namespace()` → namespace.remove(position) |
| **Remove lower priority** | New non-persistent skill pushes down others | `_update_namespace_persistence()` |

**Example Timeline**:
```
1. Start:    active_namespaces = [idle_screen]
2. Skill A:  active_namespaces = [skill_a, idle_screen]
3. Skill B:  active_namespaces = [skill_b, skill_a, idle_screen]
4. A times:  active_namespaces = [skill_b, idle_screen]
5. B times:  active_namespaces = [idle_screen]
6. B again:  active_namespaces = [skill_b, idle_screen]
```

---

## Message Routing Targets

### Where Messages Go

**Messages from NamespaceManager**:

| Message Type | Recipient | Path | Code |
|---|---|---|---|
| `mycroft.session.list.insert` | Namespace/adapters | `namespace.add()` | line 127-133 |
| `mycroft.session.list.move` | Namespace/adapters | `namespace.activate()` | line 145-152 |
| `mycroft.session.list.remove` | Namespace/adapters | `namespace.remove()` | line 166-172 |
| `mycroft.session.set` | Namespace/adapters | `namespace.load_data()` | line 186-191 |
| `mycroft.session.delete` | Namespace/adapters | `namespace.unload_data()` | line 199-204 |
| `mycroft.gui.list.insert` | Namespace/adapters | `namespace._add_pages()` | line 281-298 |
| `mycroft.gui.list.remove` | Namespace/adapters | `namespace.remove_pages()` | line 356-362 |
| `mycroft.events.triggered` | Namespace/adapters | `namespace._activate_page()` | line 338-344 |
| `gui.namespace.removed` | Core MessageBus | `_remove_namespace()` | line 859 |
| `gui.namespace.displayed` | Core MessageBus | `_emit_namespace_displayed_event()` | line 884 |

**Problem**: `namespace.send_message_to_gui()` is a **TODO** (line 108, 474) — unclear how messages actually reach GUI clients.

---

## Adapter Integration Points

The NamespaceManager calls adapters at strategic points:

### Lifecycle Callbacks

```python
# When namespace becomes active (line 741-747)
adapter.on_namespace_activated(namespace_name, site_id)

# When namespace removed from active stack (line 864-870)
adapter.on_namespace_deactivated(namespace_name)

# When session data updated (line 921-925)
adapter.on_session_update(namespace_name, filtered_data, site_id)

# When system event forwarded (line 491-497)
adapter.on_status_event(msg_type, data, site_id)

# When SYSTEM_* template is shown (line 652-659)
adapter.dispatch_template(template, skill_id, data, site_id)
```

### Status Query

```python
# Check if any GUI client is connected (line 894-897)
gui_connected = any(
    getattr(adapter, 'any_client_connected', lambda: False)()
    for adapter in self.adapters
) if self.adapters else False
```

**Note**: Adapters are **callbacks**, not bidirectional. The namespace manager tells adapters what happened; adapters cannot request state changes.

---

## Routing Key Computation

The NamespaceManager computes a `site_id` for multi-device scenarios:

**Function**: `_gui_routing_key()` (lines 605-641)

```python
# Priority order:
1. session_id == "default"     → "default"     (on-device)
2. site_id != "unknown"        → site_id       (location group)
3. else                        → session_id    (remote UUID)
```

**Example**:
- Mark2 device (no site configured) → route key = `"default"`
- Multiple speakers in "living_room" → route key = `"living_room"`
- Phone GUI (UUID, no site) → route key = session UUID

**Use**: Adapters receive `site_id` to determine which physical screen to target.

---

## Persistence & Auto-Removal

### Persistence Types

**Persistent** (stays indefinitely):
- `__idle: True` in gui.page.show message
- `persistent=True` for all pages
- No timer scheduled

**Timed** (auto-removes after duration):
- `__idle: <int>` (e.g., 30 seconds)
- `persistent=False` for pages
- Timer scheduled in `_schedule_namespace_removal()` (line 819)

### Removal Mechanics

```python
# Lines 819-836: Schedule removal
remove_namespace_timer = Timer(
    namespace.duration,  # seconds
    self._remove_namespace_via_timer,
    args=(namespace.skill_id,)
)
remove_namespace_timer.start()
remove_namespace_timers[namespace.skill_id] = remove_namespace_timer

# Lines 838-844: Timer fires
def _remove_namespace_via_timer(self, namespace_name: str):
    self._remove_namespace(namespace_name)
    self._del_namespace_in_remove_timers(namespace_name)
```

### Timer Reset on Interaction

When user interacts (line 957-961):
```python
if not namespace.persistent and self.remove_namespace_timers[namespace.skill_id]:
    self.remove_namespace_timers[namespace.skill_id].cancel()  # Cancel old timer
    self._schedule_namespace_removal(namespace)                 # Schedule new timer
```

---

## Issues & Gaps

### ⚠️ Issue 1: `send_message_to_gui()` is Not Implemented

**Location**: Line 108 (Namespace), Line 474 (NamespaceManager)

```python
def send_message_to_gui(self, message):
    pass # TODO
```

**Impact**: Unknown how messages actually reach GUI clients. Adapters have callbacks but no reverse channel.

**Status**: 🔴 **CRITICAL** — This is a dead code path. Adapters handle all messaging.

---

### ⚠️ Issue 2: `handle_send_event()` Messaging Path Unclear

**Location**: Line 515-533

```python
def handle_send_event(self, message: Message):
    # Creates mycroft.events.triggered message
    # But how does it reach GUI clients?
    message = dict(
        type='mycroft.events.triggered',
        namespace=skill_id,
        event_name=event,
        data=message.data.get('params')
    )
    self.send_message_to_gui(message)  # ← DEAD CODE (TODO)
```

**Question**: How do custom skill events reach GUI clients? Via adapters? Direct WebSocket?

---

### ⚠️ Issue 3: Adapter Method `_add_pages()` is Stubbed

**Location**: Line 281-298

```python
def _add_pages(self, new_pages: List[GuiPage]):
    LOG.debug(f"namespace \"{self.skill_id}\" current pages: {self.pages}")
    # TODO
    #for client in GUIWebsocketHandler.clients:
    #    try:
    #        LOG.debug(f"Updating {client.framework} client")
    #        client.send_gui_pages(new_pages, self.skill_id, position)
    #    except Exception as e:
    #        LOG.exception(f"Error updating {client.framework} client: {e}")
```

**Status**: Pages are added to internal `self.pages` list but messaging is unclear.

---

### ⚠️ Issue 4: `page_gained_focus` Event Listener (Line 415)

```python
self.core_bus.on("gui.page_gained_focus", self.handle_page_gained_focus)
```

**Question**: Where does this message come from? GUI clients or internal? How is it generated?

---

### ⚠️ Issue 5: `gui.namespace.displayed` Event (Line 884)

```python
self.core_bus.emit(
    Message("gui.namespace.displayed", data=message_data)
)
```

**Status**: Emitted but no known listeners (per comment on line 883).

---

## Correct Architecture Pattern

**Adapters are NOT MessageBus-driven**. The pattern is:

```
OVOS Core MessageBus
    │
    └─ NamespaceManager (listens to: gui.*, recognizer_loop:*, enclosure.*, etc.)
        │
        └─ GUI Adapter Plugins
            │
            ├─ on_namespace_activated() → dispatch_template() → renders QML/web
            ├─ on_session_update() → updates data on active page
            ├─ on_status_event() → handles system events
            └─ any_client_connected() → status query
```

**NOT**: Adapters listening directly to MessageBus.

---

## Integration with Plugin Architecture

### Entry Point: `opm.gui_adapter`

Adapters are loaded as plugins:

```python
# service.py:59-61
from ovos_plugin_manager.gui_adapter import OVOSGUIAdapterFactory
adapters = OVOSGUIAdapterFactory.create_all(config=adapter_config, bus=self.bus)
```

**Required Interface**:
```python
class GUIAdapter:
    def on_namespace_activated(self, skill_id: str, site_id: str) -> None: ...
    def on_namespace_deactivated(self, skill_id: str) -> None: ...
    def on_session_update(self, skill_id: str, data: Dict, site_id: str) -> None: ...
    def on_status_event(self, msg_type: str, data: Dict, site_id: str) -> None: ...
    def dispatch_template(self, template: str, skill_id: str, data: Dict, site_id: str) -> None: ...
    def any_client_connected(self) -> bool: ...
```

**Implementation Examples**:
- `ovos-legacy-mycroft-gui-plugin` — Reference implementation (Qt/WebSocket adapter)
- Custom adapters can render to any framework

---

## Data Flow Diagram

```
OVOS Core                          NamespaceManager              Adapters
═════════════════════════════════════════════════════════════════════════════

Skill:
gui.page.show ──────────────→ handle_show_page()
                              ├─ _ensure_namespace_exists()
                              ├─ _activate_namespace()
                              │   └─ on_namespace_activated() ──→ dispatch_template()
                              ├─ _load_pages()
                              ├─ _update_namespace_persistence()
                              │   └─ _schedule_namespace_removal()
                              └─ on_session_update() ────────→ render/update

Skill:
gui.value.set ──────────────→ handle_set_value()
                              ├─ _update_namespace_data()
                              ├─ namespace.load_data()
                              └─ on_session_update() ────────→ update data

System:
speak (etc) ─────────────────→ forward_to_gui()
                              └─ on_status_event() ──────────→ handle event

GUI Client:
page_interaction ───────────→ handle_page_interaction()
                              ├─ Reschedule timer
                              └─ namespace.page_gained_focus()

Timer:
[duration expires] ──────────→ _remove_namespace_via_timer()
                              ├─ namespace.remove()
                              └─ on_namespace_deactivated() ─→ cleanup
```

---

## Summary: Where Everything Fits

| Component | Role | Key Responsibility |
|---|---|---|
| **GUIService** | Orchestrator | Load adapters, instantiate manager, manage lifecycle |
| **NamespaceManager** | State Manager | Track active/loaded namespaces, manage lifecycle, call adapter callbacks |
| **Namespace** | Per-skill State | Hold pages, data, persistence for single skill |
| **GuiPage** | Data Class | Represent single display page |
| **Adapters** | Renderers | Receive callbacks, render to framework (Qt, web, etc.), manage clients |
| **MessageBus** | Communication | Skills emit `gui.*` messages, core forwards system events |

**The Key**: NamespaceManager is **NOT a plugin entry point**. It's a **core component** that coordinates between the MessageBus and adapter plugins.

---

## Recommendations

1. **Document messaging endpoints**: Where do `mycroft.events.triggered` messages actually go? Update `send_message_to_gui()` or remove dead code.

2. **Clarify custom events**: How do `gui.event.send` messages reach GUI clients? Is this via adapters' `on_status_event()`?

3. **Document adapter interface**: Formal interface spec for `on_namespace_activated()`, `dispatch_template()`, etc.

4. **Remove TODOs**: Implement or delete stubbed code in `_add_pages()`, `Namespace.send_message_to_gui()`.

5. **Add audit trail**: Document message lifecycle end-to-end (MessageBus → Manager → Adapter → Client).

---

**File References**:
- `service.py:29-95` — GUIService entry point and adapter loading
- `namespace.py:79-380` — Namespace class (pages, data, lifecycle)
- `namespace.py:382-1007` — NamespaceManager (state coordination, adapter callbacks)
- `page.py:1-21` — GuiPage dataclass
