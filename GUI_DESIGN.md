# OVOS GUI Refactor — Design Specification

**Version:** 1.0
**Status:** Implemented — use this document to cross-check existing work
**Scope:** GUI layer decoupling via template-based `GUIInterface` and the `opm.gui_adapter` plugin system

---

## 1. Motivation

The previous GUI system coupled skills directly to rendering technology:

- Skills shipped QML files (`gui/qt5/`) or HTML templates (`gui/py-htmx/`)
- Skills called `self.gui.show_page("MyPage.qml")` to trigger rendering
- Adding a new display backend (browser, terminal, Mark 1 face) required every skill to add new assets
- Only one rendering backend could be active at a time

The redesign removes all coupling between skill code and rendering technology:

- Skills call **typed template methods** (`show_weather()`, `show_text()`, etc.)
- All rendering is done by independently installed **adapter plugins** that receive these events
- **All loaded adapters receive every event simultaneously** — multi-modal rendering is the default

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Skill                                                              │
│    self.gui["temp"] = 22                                            │
│    self.gui.show_weather(current_temp=22, condition="Sunny", ...)   │
└─────────────────┬───────────────────────────────────────────────────┘
                  │  gui.value.set  (MessageBus)
                  │  gui.page.show  (page_names=["SYSTEM_weather"])
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ovos-gui / NamespaceManager                                        │
│    • Maintains namespace stack (LIFO active display order)          │
│    • Detects SYSTEM_* page names → dispatches to adapter plugins    │
│    • Non-SYSTEM_* page names → legacy path (unchanged)              │
└──────────┬──────────────────────────────────────┬───────────────────┘
           │ dispatch_template(...)                │ dispatch_template(...)
           ▼                                      ▼
┌──────────────────────────┐          ┌───────────────────────────────┐
│ ovos-legacy-mycroft-gui  │          │ ovos-gui-plugin-pyhtmx        │
│  Tornado WS → Qt client  │          │  FastAPI/SSE → browser        │
└──────────────────────────┘          └───────────────────────────────┘
           │                                      │
    mycroft-gui protocol              HTML + HTMX + SSE
           ▼                                      ▼
     Qt/QML display                         Web browser
```

**Key invariants:**
1. `ovos-gui` runs **no WebSocket server**. The legacy WS on port 18181 is started exclusively by `ovos-legacy-mycroft-gui-plugin`.
2. When no adapter is installed, all `GUIInterface` calls are silent no-ops. Skills never crash on headless devices.
3. The namespace stack and idle-display logic in `NamespaceManager` are unchanged for the non-template (legacy) path.

---

## 3. Package Dependency Graph

```
ovos-gui-api-client          ← standalone; GUIInterface + PageTemplates
      ↑
ovos-workshop                ← OVOSSkill.gui = GUIInterface(skill_id, bus)
      │  emits gui.value.set + gui.page.show(SYSTEM_*)
      ▼
ovos-gui                     ← NamespaceManager; no WS server
      │  via OVOSGUIAdapterFactory (entry point group: opm.gui_adapter)
      ├── ovos-legacy-mycroft-gui-plugin  ← Tornado WS → Qt/mycroft-gui
      └── ovos-gui-plugin-pyhtmx          ← FastAPI/SSE → browser

ovos-plugin-manager          ← AbstractGUIPlugin + OVOSGUIAdapterFactory
```

---

## 4. GUIInterface (`ovos-gui-api-client`)

**Package:** `ovos-gui-api-client`
**Module:** `ovos_gui_api_client`
**Class:** `GUIInterface`

### 4.1 Construction

```python
GUIInterface(skill_id: str, bus=None, config: dict = None)
```

- `skill_id` doubles as the **namespace** in all GUI protocol messages.
- In `ovos-workshop`, `OVOSSkill.gui` is a `GUIInterface` bound to `self.skill_id`.
- The bus may be set later via `set_bus(bus)`.

### 4.2 Session Data

Session data is a key-value store synced to `ovos-gui` via the `gui.value.set` message.

```python
self.gui["key"] = value          # triggers gui.value.set immediately when a page is active
self.gui.update({"a": 1, "b": 2})  # batched update — single sync message
value = self.gui["key"]
value = self.gui.get("key", default)
```

- Assigning a `dict` value wraps it in `_GUIDict`, which propagates mutations (nested key changes) back as sync events automatically.
- Reserved keys `__from` and `__idle` must not be used by skills; they are stripped before delivery to adapters.
- **Session data is not cleared between template calls.** Values accumulate until `release()` is called.

### 4.3 Template Methods

All 21 template methods follow the same pattern:

1. Validate / transform arguments (e.g., base64-encode local image files)
2. Set affected session data keys via `self[key] = value`
3. Call `_show_page(PageTemplates.SYSTEM_*)` which emits `gui.page.show`

Skills **must not** call `show_page()` directly. Use the typed methods below.

| Method | Template constant | Key session data keys |
|---|---|---|
| `show_idle()` | `SYSTEM_idle` | — |
| `show_loading(text)` | `SYSTEM_loading` | `label` |
| `show_status(text, success)` | `SYSTEM_status` | `label`, `success` |
| `show_error(text, detail)` | `SYSTEM_error` | `label`, `detail` |
| `show_text(text, title)` | `SYSTEM_text` | `text`, `title` |
| `show_image(url, caption, title, fill)` | `SYSTEM_image` | `image`, `caption`, `title`, `fill` |
| `show_animated_image(url, ...)` | `SYSTEM_animated_image` | same as image |
| `show_html(html)` | `SYSTEM_html` | `html` |
| `show_url(url)` | `SYSTEM_url` | `url` |
| `show_list(items, title)` | `SYSTEM_list` | `title`, `items` |
| `show_grid(items, title)` | `SYSTEM_grid` | `title`, `items` |
| `show_table(columns, rows, title)` | `SYSTEM_table` | `title`, `columns`, `rows` |
| `show_audio_player(title, artist, album, image, playing, position, duration)` | `SYSTEM_audio_player` | all of the above |
| `show_video_player(uri, title, playing)` | `SYSTEM_video_player` | `uri`, `title`, `playing` |
| `show_clock()` | `SYSTEM_clock` | — (JS-driven) |
| `show_timer(end_time, label, count_up)` | `SYSTEM_timer` | `end_time`, `label`, `count_up` |
| `show_weather(current_temp, min_temp, max_temp, condition, icon, location)` | `SYSTEM_weather` | all of the above |
| `show_map(latitude, longitude, zoom, label)` | `SYSTEM_map` | `latitude`, `longitude`, `zoom`, `label` |
| `show_confirm(question)` | `SYSTEM_confirm` | `question` |
| `show_select(items, prompt)` | `SYSTEM_select` | `prompt`, `items` |
| `show_face(awake)` | `SYSTEM_face` | `sleeping` |

### 4.4 Image Delivery

`show_image` and `show_animated_image` accept:

- **HTTP(S) URL** — used as-is in the session data
- **Absolute local file path** — the file is read and base64-encoded into a `data:<mime>;base64,...` URI before being written to session data
- **`data:` URI** — passed through unchanged

This means adapters always receive either a URL or a `data:` URI. No adapter needs to read the local filesystem or mount a file-serving endpoint.

```python
# Implementation in show_image:
if not url.startswith(("http://", "https://", "data:")):
    if not os.path.isfile(url):
        LOG.error(f"Image not found: '{url}'")
        return
    mime, _ = mimetypes.guess_type(url)
    mime = mime or "image/png"
    with open(url, "rb") as f:
        url = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
self["image"] = url
```

Skills that reference local image assets **must** pass an absolute path. Use `self.root_dir` to construct it:

```python
self.gui.show_image(os.path.join(self.root_dir, "gui", "all", "logo.png"))
```

### 4.5 Auxiliary Types

| Type | Purpose |
|---|---|
| `PageTemplates` | Enum of all 21 `SYSTEM_*` template name strings |
| `FillMode` | Enum: `FIT`, `CROP`, `STRETCH` — for `show_image` `fill` arg |
| `ListItem` | Dataclass: `title`, `subtitle`, `image` — items for `show_list` |
| `GridItem` | Dataclass: `image`, `title` — tiles for `show_grid` |
| `SelectItem` | Dataclass: `label`, `value` — options for `show_select` |

### 4.6 Lifecycle

```python
gui.release()       # Clear the namespace from the display stack (skill done)
gui.register_handler(event, callback)  # Listen for GUI-originated events
```

`release()` emits `gui.clear.namespace` which removes the skill from the `NamespaceManager` active stack.

### 4.7 GUI Availability Guard

```python
if self.gui.connected:
    ...             # True if any adapter has a connected client
if self.gui.gui_disabled:
    ...             # True if gui is disabled in mycroft.conf
```

Skills may optionally guard display calls with `self.gui.connected`.

---

## 5. Bus Messages

### 5.1 Skill → ovos-gui

| Message type | Emitted by | Purpose |
|---|---|---|
| `gui.value.set` | `GUIInterface._sync_data()` | Push session data key-values to namespace |
| `gui.page.show` | `GUIInterface._show_page()` | Request display of named page(s) |
| `gui.clear.namespace` | `GUIInterface.release()` | Remove skill from active namespace stack |
| `gui.page.delete` | `GUIInterface._remove_page()` | Remove specific pages from namespace |
| `gui.event.send` | `GUIInterface._emit_gui_event()` | Forward GUI-originated event to skill |

### 5.2 Key message payloads

**`gui.value.set`**
```json
{
  "__from": "skill.id",
  "key1": "value1",
  "key2": 42
}
```

**`gui.page.show`** (template path — triggers adapter dispatch)
```json
{
  "__from": "weather.openvoiceos",
  "page_names": ["SYSTEM_weather"],
  "__idle": 30
}
```

**`gui.page.show`** (legacy path — non-`SYSTEM_*` name)
```json
{
  "__from": "myskill.author",
  "page_names": ["MyPage.qml"],
  "__idle": true
}
```

### 5.3 ovos-gui → skills / core

| Message type | Emitted by | Purpose |
|---|---|---|
| `gui.status.request.response` | `NamespaceManager.handle_status_request` | Reply to GUI connectivity query |
| `gui.namespace.removed` | `NamespaceManager._remove_namespace` | Notify core that namespace was deactivated |
| `gui.namespace.displayed` | `NamespaceManager._emit_namespace_displayed_event` | Notify which namespace is currently visible |

### 5.4 GUI status request

Any component can check GUI connectivity:

```python
bus.emit(Message("gui.status.request"))
# Reply: gui.status.request.response  {"connected": true/false}
```

`NamespaceManager` answers `True` if **any** loaded adapter's `any_client_connected()` returns `True`.

---

## 6. NamespaceManager (`ovos-gui`)

**File:** `ovos_gui/namespace.py`
**Class:** `NamespaceManager`

### 6.1 Construction

```python
NamespaceManager(core_bus: MessageBusClient, adapters: list = None)
```

`adapters` is a list of `AbstractGUIPlugin` instances loaded at startup by `GUIService._load_adapter_plugins()`.

### 6.2 GUI routing key — `session_id`

The routing identifier is the **`session_id`**, read from the message's session
context (`message.context["session"]["session_id"]`). There is no separate
location dimension. A shared/multi-room screen is expressed by clients
**sharing the same `session_id`**. The on-device default is just
`session_id == "default"`.

| Scenario | `session_id` | Example |
|---|---|---|
| On-device display | `"default"` | Mark 2, laptop with local listener |
| Shared screen group | a shared id | several screens connect with the same id |
| Standalone remote GUI | the remote's session id (e.g. a UUID) | phone GUI on a remote OVOS server |

`NamespaceManager._session_id(message)` extracts it (defaulting to `"default"`).
Each `session_id` owns an independent namespace stack; the `session_id` is
forwarded to every adapter so adapters can target the matching client(s).

**Routing rules:**
- Template events and session data carry the `session_id`; adapters deliver
  them to clients on that session.
- Namespace removal and status events (wakeword, speaking, etc.) are
  system-wide signals; adapters typically broadcast them to all clients.

### 6.3 Template dispatch

`handle_show_page` is the central handler for `gui.page.show`. The first page
name must be a `SYSTEM_*` template:

- Starts with `"SYSTEM_"` → **template path**: dispatches to all adapters with
  the `session_id`, then activates the namespace on that session's stack.
- Otherwise → rejected (custom QML is not supported).

```python
session_id = self._session_id(message)
session = self.get_session(session_id)
namespace = self._ensure_namespace_exists(namespace_name, session)
data = {k: v for k, v in namespace.data.items()}
for template in page_ids_to_show:
    self._dispatch_template_to_adapters(template, namespace_name, data, session_id)
with namespace_lock:
    if not session.active_namespaces or session.active_namespaces[0].skill_id != namespace_name:
        self._activate_namespace(namespace_name, session, session_id)
    self._update_namespace_persistence(persistence, session)
```

### 6.4 Session data forwarding

Every `gui.value.set` message calls `adapter.on_session_update(skill_id, filtered_data, session_id)` on all adapters after updating the internal namespace data. `__from` and `__idle` reserved keys are stripped before delivery.

### 6.5 Lifecycle hook invocation

| Internal event | Adapter hook called | Routing |
|---|---|---|
| Namespace moves to top of active stack | `on_namespace_activated(skill_id, session_id)` | per-session |
| Namespace removed from active stack | `on_namespace_deactivated(skill_id, session_id)` | per-session |
| `gui.value.set` received | `on_session_update(skill_id, data, session_id)` | per-session |
| Status event forwarded | `on_status_event(event_name, data, session_id)` | broadcast all |

Status events (wakeword, speaking, etc.) are system-wide signals; adapters
broadcast them to all clients regardless of session.

### 6.6 Namespace persistence

The `__idle` field in `gui.page.show` controls how long the namespace stays visible:

| `__idle` value | Behaviour |
|---|---|
| `true` | Persistent — stays until `gui.clear.namespace` |
| `30` (int) | Visible for 30 seconds, then auto-removed |
| omitted / `null` | Default: 30 seconds |

This logic is maintained for both the template path and the legacy path.

---

## 7. AbstractGUIPlugin (`ovos-plugin-manager`)

**File:** `ovos_plugin_manager/templates/gui.py`
**Class:** `AbstractGUIPlugin`
**Entry point group:** `opm.gui_adapter`

### 7.1 Construction

```python
AbstractGUIPlugin(config: dict, bus: MessageBusClient = None)
```

- `config` is the plugin-specific section from `mycroft.conf → gui.adapters.<entry-point-name>`
- `bus` is the shared `MessageBusClient` from `GUIService`

### 7.2 Template handlers (21)

Each handler defaults to a no-op. Subclasses override only those they support. Handlers are invoked via `dispatch_template()` which catches and logs any exceptions, so a broken handler never affects other adapters.

```python
def handle_show_text(self, skill_id: str, data: dict, session_id: str = "default") -> None: ...
def handle_show_weather(self, skill_id: str, data: dict, session_id: str = "default") -> None: ...
# ... 19 others — see AbstractGUIPlugin._TEMPLATE_HANDLERS
```

`session_id` is the **routing key** read from the message context (see §6.2).
Adapters use it to deliver the update only to the matching client(s); shared
screens share a `session_id`.

The full handler-to-template mapping is maintained in `AbstractGUIPlugin._TEMPLATE_HANDLERS`:

```python
_TEMPLATE_HANDLERS = {
    "SYSTEM_idle":           "handle_show_idle",
    "SYSTEM_loading":        "handle_show_loading",
    "SYSTEM_status":         "handle_show_status",
    "SYSTEM_error":          "handle_show_error",
    "SYSTEM_text":           "handle_show_text",
    "SYSTEM_image":          "handle_show_image",
    "SYSTEM_animated_image": "handle_show_animated_image",
    "SYSTEM_list":           "handle_show_list",
    "SYSTEM_grid":           "handle_show_grid",
    "SYSTEM_table":          "handle_show_table",
    "SYSTEM_html":           "handle_show_html",
    "SYSTEM_url":            "handle_show_url",
    "SYSTEM_audio_player":   "handle_show_audio_player",
    "SYSTEM_video_player":   "handle_show_video_player",
    "SYSTEM_media_player":   "handle_show_media_player",
    "SYSTEM_clock":          "handle_show_clock",
    "SYSTEM_timer":          "handle_show_timer",
    "SYSTEM_weather":        "handle_show_weather",
    "SYSTEM_map":            "handle_show_map",
    "SYSTEM_confirm":        "handle_show_confirm",
    "SYSTEM_select":         "handle_show_select",
    "SYSTEM_face":           "handle_show_face",
}
```

### 7.3 Lifecycle hooks

```python
def on_namespace_activated(self, skill_id: str, session_id: str = "default") -> None: ...
def on_namespace_deactivated(self, skill_id: str, session_id: str = "default") -> None: ...
def on_idle(self) -> None: ...
def on_session_update(self, skill_id: str, data: dict, session_id: str = "default") -> None: ...
def on_status_event(self, event_name: str, data: dict, session_id: str = "default") -> None: ...
```

`on_namespace_deactivated` and `on_status_event` are system-wide signals; the
`session_id` is accepted for API consistency, but adapters should broadcast
these to all connected clients regardless of session.

### 7.4 Connection status

```python
def any_client_connected(self) -> bool: ...
```

Implement this to participate in `gui.status.request` responses. Return `True` if at least one client is actively connected. `NamespaceManager` calls this via `getattr(..., lambda: False)()` so it is safe to leave unimplemented.

### 7.5 Registration

```toml
# pyproject.toml
[project.entry-points."opm.gui_adapter"]
"my-adapter" = "my_package:MyAdapterClass"
```

```python
# setup.py (legacy)
entry_points={
    "opm.gui_adapter": ["my-adapter = my_package:MyAdapterClass"]
}
```

---

## 8. Plugin Discovery and Loading (`ovos-plugin-manager`)

**File:** `ovos_plugin_manager/gui.py`

```python
find_gui_adapter_plugins() -> Dict[str, Type[AbstractGUIPlugin]]
load_gui_adapter_plugin(module_name) -> Optional[Type[AbstractGUIPlugin]]

OVOSGUIAdapterFactory.create_all(bus=None, config=None) -> List[AbstractGUIPlugin]
```

`GUIService._load_adapter_plugins()` calls `create_all` with:
- `bus = self.bus` (the shared MessageBusClient)
- `config = mycroft.conf["gui"]["adapters"]`

`create_all` never raises: plugins that raise during `__init__` are skipped and
logged, and a headless device with no adapters installed gets an empty list.
The GUI service then degrades to no-op dispatch instead of crashing.

`PluginTypes.GUI_ADAPTER = "opm.gui_adapter"` is defined in `ovos_plugin_manager/utils/__init__.py`.

---

## 9. Built-in Adapters

### 9.1 Legacy Qt adapter — `ovos-legacy-mycroft-gui-plugin`

| Property | Value |
|---|---|
| Entry point name | `ovos-legacy-mycroft-gui` |
| Class | `LegacyMycoftGuiPlugin(AbstractGUIPlugin)` |
| Transport | Tornado WebSocket on port 18181 |
| Clients | Qt/QML via `mycroft-gui-qt5` library |
| Protocol | Mycroft GUI WebSocket protocol (see `docs/701-gui_protocol.md`) |

**What it does:**
- On `__init__`, starts the Tornado WS server (previously run by `ovos-gui` itself)
- For each `handle_show_*` call, resolves the matching bundled QML file from its `ui/` directory and sends `mycroft.gui.list.insert` + `mycroft.session.set` messages only to clients whose `session_id` matches via `send_to_clients_for_session(session_id, msg)`
- Status events and namespace removal are broadcast to **all** connected Qt clients via `send_to_all_clients(msg)` — these are system-wide signals
- Each Qt client announces its `session_id` in the `mycroft.gui.connected` handshake: `{"session_id": "default"}` on-device, a shared id for a multi-room screen group, or the remote session id for a standalone remote GUI
- Implements `any_client_connected()` based on active WS connections
- Skills provide **no QML** — the 21 QML stubs are bundled inside this plugin

### 9.2 PyHTMX adapter — `ovos-gui-plugin-pyhtmx`

| Property | Value |
|---|---|
| Entry point name | `ovos-gui-plugin-pyhtmx` |
| Class | `PyHTMXGUIPlugin(AbstractGUIPlugin)` |
| Transport | FastAPI/uvicorn HTTP server with SSE push |
| Clients | Any web browser |
| Config keys | `host` (default `0.0.0.0`), `port` (default `8080`) |

**What it does:**
- On `__init__`, creates a `GUIManager` and starts FastAPI/uvicorn in a daemon thread
- For each `handle_show_*` call, instantiates the matching `Page` subclass from `templates/__init__.py` and calls `GUIManager.show_template_page(..., session_id=session_id)`
- DOM updates are pushed only to browser tabs whose `session_id` matches via per-tab SSE queues; status events broadcast to all tabs
- Each browser tab declares its `session_id` at `GET /?session_id=` (default `"default"`) and gets a dedicated SSE endpoint `/updates/{session_id}`
- `Renderer.send(data, session_id=None)` delivers to matching tabs (`None` = broadcast all)
- Implements `any_client_connected()` by checking `global_renderer._clients`
- Touch events from `ConfirmPage` / `SelectPage` call back to OVOS via `self.bus.emit()`
- Tabs that stop sending pings are cleaned up after 30 s (`_check_disconnected` daemon thread)

**Server routes:**
| Route | Purpose |
|---|---|
| `GET /?session_id=default` | Serve initial HTML; register browser tab with a `session_id` (default: `"default"`) |
| `GET /updates/{session_id}` | Per-tab SSE stream for DOM patch events |
| `GET /local-event/{id}` | HTMX local callback — returns HTML fragment |
| `POST /global-event/{id}` | HTMX global callback — no body returned |
| `POST /ping/{session_id}` | Browser keepalive; sessions without pings time out after 30 s |
| `GET /assets/*` | Static CSS/JS/font files |

**`session_id` values (query parameter `session_id`):**

| Value | Meaning |
|---|---|
| `"default"` | On-device display (Mark 2, laptop) — default if not specified |
| any shared string | Multi-room screen group — tabs sharing the id share state |
| remote session id | Standalone remote GUI (phone/tablet) — matches the OVOS session id |

---

## 10. Configuration

All adapter configuration lives under `gui.adapters.<entry-point-name>` in `mycroft.conf`:

```json
{
  "gui": {
    "idle_display_skill": "skill-ovos-homescreen.openvoiceos",
    "adapters": {
      "ovos-legacy-mycroft-gui": {
        "host": "0.0.0.0",
        "base_port": 18181,
        "route": "/gui",
        "ssl": false
      },
      "ovos-gui-plugin-pyhtmx": {
        "host": "0.0.0.0",
        "port": 8080
      }
    }
  }
}
```

---

## 11. Skill Contract

### 11.1 What skills must do

- Call typed `show_*()` template methods on `self.gui` — no `show_page()` calls
- Use `self.gui["key"] = value` for session data that needs live updates (e.g., playback position)
- Pass **absolute file paths** for local images (construct with `os.path.join(self.root_dir, ...)`)
- Call `self.gui.release()` when done displaying

### 11.2 What skills must not do

- Ship `gui/qt5/`, `gui/qt6/`, or `gui/py-htmx/` framework asset directories
- Call `self.gui.show_page()`, `self.gui.remove_page()`, or access `self.gui._pages`
- Block waiting for a GUI event — voice is primary, touch is supplementary
- Assume a display is present — guard with `if self.gui.connected:` where appropriate

### 11.3 Retained from old API (still valid)

- `self.gui["key"] = value` — session data assignment
- `self.gui.get("key", default)` — session data read
- `self.gui.release()` — clear namespace
- `self.gui.register_handler(event, callback)` — listen for GUI events
- `self.gui.connected` — check if any display is available
- `self.gui.gui_disabled` — check if GUI is disabled in config
- `gui/all/` directories — image/sound assets may be kept; reference via absolute path

### 11.4 Voice-first principles

- Touch is a shortcut, never the only interaction path
- Some clients are display-only (no touch, no keyboard)
- Skills must never block waiting for a GUI event
- The GUI accompanies speech; it does not drive interaction

---

## 12. Migrated Skills Reference

The following skills have been fully migrated to the template API:

| Skill | Old pattern | New calls | `gui/qt5/` removed |
|---|---|---|---|
| `ovos-skill-date-time` | `show_page("date.qml")`, `show_page("time.qml")` | `show_text(date_str)`, `show_clock()` | N/A (never had qt5/) |
| `ovos-skill-weather` | `show_page("CurrentWeather.qml")`, etc. | `show_weather(...)`, `show_list(...)` | Yes |
| `ovos-skill-alerts` | `show_page("Timer.qml")`, `show_page("ListView.qml")` | `show_timer(...)`, `show_list(...)` | Yes |
| `ovos-skill-ddg` | `show_page("DuckDelegate.qml")` | `show_image(image, caption=summary)` | Yes |
| `ovos-skill-wikipedia` | `show_animated_image("jumping.gif")` (relative) | absolute path via `self.root_dir` | N/A |
| `ovos-skill-confucius-quotes` | `show_image("confucius.jpg")` (relative) | absolute path via `self.root_dir` | N/A |
| `ovos-skill-iss-location` | `show_image(imgLink)` | unchanged — generates absolute `/tmp/` paths | N/A |
| `ovos-skill-laugh` | `show_image(image)` (absolute paths already) | unchanged | N/A |

Skills that are **not** in scope (custom QML voice apps, shell companion):

- `ovos-gui-plugin-shell-companion` — custom shell UI; uses legacy `show_page("AdditionalSettings")` for a Qt-specific settings panel. This is a platform plugin, not a skill, and is intentionally outside this migration.
- `ovos-skill-homescreen` — custom shell homescreen; sets session data for ovos-shell but makes no `show_page()` calls. Left as-is.
- OCP skills (`ovos-skill-spotify`, `ovos-skill-tunein`, etc.) — media providers; never call GUI methods. `show_audio_player()` is called by the OCP audio service, not by individual media skills.

---

## 13. Verification Checklist

Use this checklist to confirm the implementation matches this spec:

### ovos-plugin-manager

- [ ] `PluginTypes.GUI_ADAPTER = "opm.gui_adapter"` exists in `ovos_plugin_manager/utils/__init__.py`
- [ ] `AbstractGUIPlugin` in `templates/gui.py` has all 21 `handle_show_*` methods (defaulting to no-op)
- [ ] `AbstractGUIPlugin._TEMPLATE_HANDLERS` maps all 21 `SYSTEM_*` strings to handler names
- [ ] `dispatch_template()` catches and logs exceptions without re-raising
- [ ] `on_namespace_activated`, `on_namespace_deactivated`, `on_idle`, `on_session_update`, `on_status_event` all exist (defaulting to no-op)
- [ ] `OVOSGUIAdapterFactory.create_all()` in `gui_adapter.py` loads all installed plugins
- [ ] Failed plugin instantiation is caught, logged, and skipped (other plugins continue)

### ovos-gui

- [ ] `ovos_gui/bus.py` does not exist (deleted — Tornado WS moved to legacy plugin)
- [ ] `NamespaceManager.__init__` does NOT call `create_gui_service()` or start any WS server
- [ ] `NamespaceManager` constructor accepts `adapters: list = None`
- [ ] `_session_id(message)` returns `message.context["session"]["session_id"]`, defaulting to `"default"` (the routing key is the session_id; no `site_id`)
- [ ] `handle_show_page` routes `SYSTEM_*` page names to `_dispatch_template_to_adapters(template, skill_id, data, session_id)` and returns early (rejects non-template names)
- [ ] `_dispatch_template_to_adapters` calls `adapter.dispatch_template(template, skill_id, data, session_id)` for each adapter
- [ ] `handle_set_value` calls `adapter.on_session_update(namespace_name, filtered_data, session_id)` for each adapter (after stripping reserved keys)
- [ ] `_activate_namespace(...)` calls `adapter.on_namespace_activated(skill_id, session_id)` for each adapter
- [ ] `_remove_namespace` calls `adapter.on_namespace_deactivated(skill_id, session_id)` for each adapter
- [ ] `handle_status_request` uses `adapter.any_client_connected()` (not a Tornado client list)
- [ ] Status events from `_define_messages_to_forward` call `adapter.on_status_event(event_name, data, session_id)` for each adapter
- [ ] No `gui.page.delete*` handlers and no `GuiPage`/page model (template-only namespaces)

### ovos-gui-api-client

- [ ] `GUIInterface` is the class exported from `ovos_gui_api_client`
- [ ] All 21 `show_*()` methods exist and set the correct session data keys before calling `_show_page(PageTemplates.SYSTEM_*)`
- [ ] `show_image()` and `show_animated_image()` base64-encode local file paths into `data:` URIs
- [ ] `show_image()` with a non-existent local path logs an error and returns without emitting
- [ ] `PageTemplates`, `FillMode`, `ListItem`, `GridItem`, `SelectItem` are all exported
- [ ] `gui["key"] = dict_value` wraps the value in `_GUIDict` (nested mutation triggers sync)
- [ ] `gui.connected` queries `gui.status.request` / `gui.status.request.response`
- [ ] `gui.gui_disabled` reads `config.get("disable_gui", False)`

### ovos-workshop

- [ ] `OVOSSkill.gui` is a `GUIInterface` from `ovos_gui_api_client`, not `ovos_bus_client`
- [ ] `requirements.txt` includes `ovos-gui-api-client>=0.1.0,<1.0.0`

### ovos-legacy-mycroft-gui-plugin

- [ ] Inherits from `AbstractGUIPlugin`
- [ ] Registered under entry point group `opm.gui_adapter`
- [ ] Starts Tornado WS on port 18181 in `__init__` (not on module import)
- [ ] `QtGUIWebSocketHandler` has `_session_id` attribute set from `mycroft.gui.connected` handshake (`session_id` field, default `"default"`)
- [ ] `send_to_clients_for_session(session_id, msg)` delivers only to clients where `client.session_id == session_id` (exact match — `"default"` is NOT a wildcard)
- [ ] `send_to_all_clients(msg)` used for status events and namespace removal (system-wide)
- [ ] All `handle_show_*` methods have signature `(self, skill_id, data, session_id="default")` and use `send_to_clients_for_session`
- [ ] `on_namespace_activated(skill_id, session_id="default")` uses `send_to_clients_for_session`
- [ ] `on_namespace_deactivated(skill_id, session_id="default")` uses `send_to_all_clients`
- [ ] `on_status_event(event_name, data, session_id="default")` uses `send_to_all_clients` (always broadcast)
- [ ] All 21 `handle_show_*` methods implemented; each resolves a bundled QML file from `ui/`
- [ ] Skills supply no QML — all 21 QML stubs are bundled inside this plugin's `ui/` directory
- [ ] Implements `any_client_connected()` based on active WS connections

### ovos-gui-plugin-pyhtmx

- [ ] Inherits from `AbstractGUIPlugin`
- [ ] Registered under entry point group `opm.gui_adapter` as `pyhtmx_gui:PyHTMXGUIPlugin`
- [ ] Starts FastAPI/uvicorn in a daemon thread in `__init__`
- [ ] `app.py` has NO `/cache` static mount
- [ ] `gui_client.py` does not exist (deleted)
- [ ] `GET /` accepts `session_id: str = "default"` query parameter; patches `sse-connect` to `/updates/{session_id}` and ping URL to `/ping/{session_id}`
- [ ] `GET /updates/{session_id}` serves a dedicated SSE queue per browser tab
- [ ] `EventSender` uses `{session_id: Queue}` dict; `send(msg, session_ids=None)` delivers to matching tabs (`None` = broadcast all)
- [ ] `Renderer.send(data, session_id=None)` — `None` broadcasts; string routes to matching sessions only
- [ ] `_check_disconnected` daemon cleans up sessions that stop pinging after 30 s
- [ ] All `handle_show_*` methods have signature `(self, skill_id, data, session_id="default")`; pass `session_id` to `show_template_page`
- [ ] `on_namespace_activated(skill_id, session_id="default")` passes `session_id` to `GUIManager.show`
- [ ] `on_status_event(event_name, data, session_id="default")` passes `session_id=None` to `GUIManager.update_status` (always broadcast)
- [ ] `templates/__init__.py` defines all `Page` subclasses and `TEMPLATE_PAGE_MAP`
- [ ] `ConfirmPage` and `SelectPage` accept `skill_id` and call back to OVOS bus on touch
- [ ] `app.set_plugin(plugin)` must be called before uvicorn starts
- [ ] Implements `any_client_connected()` via the renderer's session map
- [ ] `on_namespace_activated`, `on_namespace_deactivated`, `on_session_update`, `on_status_event` all implemented

### Skills

- [ ] No `gui/qt5/` or `gui/qt6/` or `gui/py-htmx/` directories in any skill
- [ ] No `self.gui.show_page()` calls in any skill
- [ ] No `self.gui.remove_page()` calls in any skill
- [ ] No `self.gui._pages` access in any skill
- [ ] Local image paths passed to `show_image()` are absolute (constructed via `self.root_dir`)

---

## 14. Adding a New Adapter

Minimal implementation of a terminal-rendering adapter:

```python
# my_package/__init__.py
from ovos_plugin_manager.templates.gui import AbstractGUIPlugin

class TerminalGUIPlugin(AbstractGUIPlugin):
    def __init__(self, config, bus=None):
        super().__init__(config, bus)
        # start any server / rendering pipeline here

    def handle_show_text(self, skill_id: str, data: dict, session_id: str = "default") -> None:
        # session_id is the routing key — use it to target specific terminals if applicable
        print(f"[{skill_id}@{session_id}] {data.get('title', '')}: {data.get('text', '')}")

    def handle_show_weather(self, skill_id: str, data: dict, session_id: str = "default") -> None:
        print(f"[{skill_id}@{session_id}] {data['location']}: {data['current_temp']}° {data['condition']}")

    def on_status_event(self, event_name: str, data: dict, session_id: str = "default") -> None:
        # Status events are system-wide — ignore session_id and broadcast to all terminals
        print(f"[status] {event_name}")

    def any_client_connected(self) -> bool:
        return True  # terminal is always "connected"
```

```toml
# pyproject.toml
[project.entry-points."opm.gui_adapter"]
"my-terminal-gui" = "my_package:TerminalGUIPlugin"
```

```json
// mycroft.conf
{
  "gui": {
    "adapters": {
      "my-terminal-gui": {}
    }
  }
}
```

No further integration is needed. `ovos-gui` will discover and load the plugin at startup, and will call its handlers for every template event.
