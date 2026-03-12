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
| `show_media_player(now_playing, playlist, search_results, state)` | `SYSTEM_media_player` | see §4.3a |
| `show_clock()` | `SYSTEM_clock` | — (JS-driven) |
| `show_timer(end_time, label, count_up)` | `SYSTEM_timer` | `end_time`, `label`, `count_up` |
| `show_weather(current_temp, min_temp, max_temp, condition, icon, location)` | `SYSTEM_weather` | all of the above |
| `show_map(latitude, longitude, zoom, label)` | `SYSTEM_map` | `latitude`, `longitude`, `zoom`, `label` |
| `show_confirm(question)` | `SYSTEM_confirm` | `question` |
| `show_select(items, prompt)` | `SYSTEM_select` | `prompt`, `items` |
| `show_face(awake)` | `SYSTEM_face` | `sleeping` |

### 4.3a `show_media_player` — OCP Media Player Template

**Caller:** `ovos-media` (`OCPMediaPlayer._update_gui()`) — the only component that calls this template.
Individual media backend plugins (`AudioService`, `VideoService`, `WebService`) do **not** call any GUI template directly; they handle audio/video/web rendering only.

**Purpose:** Render the full OCP media player UI: currently-playing metadata, playback controls, playlist queue, and search results — equivalent to the historical OCP QML player screen. Adapters implement this as a single multi-view surface (tabs, panels, or pages).

**Signature:**

```python
def show_media_player(
    self,
    now_playing: dict | None = None,
    playlist: list[dict] | None = None,
    search_results: list[dict] | None = None,
    state: str = "playing",  # "playing" | "paused" | "stopped" | "loading" | "error"
) -> None:
```

**Session data keys written by `show_media_player`:**

| Key | Type | Description |
|---|---|---|
| `ocp_title` | `str` | Track title |
| `ocp_artist` | `str` | Artist name |
| `ocp_album` | `str` | Album name |
| `ocp_image` | `str` | Album art URL or `data:` URI |
| `ocp_uri` | `str` | Currently playing URI (for deep-link or progress reporting) |
| `ocp_position` | `int` | Playback position in milliseconds |
| `ocp_duration` | `int` | Track duration in milliseconds; `-1` if unknown/live |
| `ocp_playback_state` | `str` | `"playing"` / `"paused"` / `"stopped"` / `"loading"` / `"error"` |
| `ocp_playlist` | `list[dict]` | Ordered queue; each item: `{title, artist, image, uri, duration}` |
| `ocp_search_results` | `list[dict]` | Search result entries; each: `{title, artist, image, uri, skill_id, match_confidence}` |
| `ocp_playlist_position` | `int` | Index of the currently playing track in `ocp_playlist` |

**`now_playing` dict keys** (subset of `NowPlaying` serialisation):

```python
{
    "title": str,
    "artist": str,
    "album": str,
    "image": str,           # URL or data: URI
    "uri": str,
    "position": int,        # milliseconds
    "duration": int,        # milliseconds; -1 for live streams
}
```

**Playlist / search result item dict:**

```python
# playlist item
{"title": str, "artist": str, "image": str, "uri": str, "duration": int}

# search result item
{"title": str, "artist": str, "image": str, "uri": str,
 "skill_id": str, "match_confidence": float}
```

**`state` values and their UI meaning:**

| State | Adapter behaviour |
|---|---|
| `"playing"` | Show play controls; scrubbar advancing |
| `"paused"` | Show play controls; scrubbar frozen |
| `"stopped"` | Show idle/empty player with playlist visible |
| `"loading"` | Show spinner over artwork; disable seek/skip |
| `"error"` | Show error indicator; keep last metadata visible |

**How adapters should render the three views:**

Adapters receive all three data sets in every call. They should provide navigation between:
1. **Now Playing** — large artwork, title/artist, scrubbar, prev/play-pause/next, shuffle/repeat controls
2. **Queue** — ordered list of `ocp_playlist` items; tap to jump; current item highlighted
3. **Search Results** — grid or list of `ocp_search_results`; tap to enqueue or play immediately

The adapter decides the UX (tabs, swipe panels, separate pages). `ovos-media` only pushes data.

**Interaction events (GUI → OCP bus):**

Adapters emit these bus messages in response to user touch:

| User action | Bus message emitted | Data |
|---|---|---|
| Play/Pause button | `ovos.common_play.play_pause` | `{}` |
| Next button | `ovos.common_play.next` | `{}` |
| Previous button | `ovos.common_play.prev` | `{}` |
| Seek scrubbar | `ovos.common_play.seek` | `{"position": ms}` |
| Tap playlist item | `ovos.common_play.playlist.play_index` | `{"index": int}` |
| Tap search result | `ovos.common_play.search.play` | `{"uri": str, "skill_id": str}` |
| Shuffle toggle | `ovos.common_play.shuffle.toggle` | `{}` |
| Repeat toggle | `ovos.common_play.repeat.toggle` | `{}` |

**Example call from `ovos-media`:**

```python
self.gui.show_media_player(
    now_playing={
        "title": "Bohemian Rhapsody",
        "artist": "Queen",
        "album": "A Night at the Opera",
        "image": "https://…/cover.jpg",
        "uri": "spotify:track:xyz",
        "position": 42000,
        "duration": 354000,
    },
    playlist=[
        {"title": "Don't Stop Me Now", "artist": "Queen",
         "image": "…", "uri": "spotify:track:abc", "duration": 209000},
    ],
    search_results=[],
    state="playing",
)
```

**Responsibility boundary:**

- `ovos-media` calls `show_media_player()` to push metadata and state. It never calls `show_video_player()` or `show_url()`.
- Individual backend plugins (`VideoService`, `WebService` subclasses) may call `show_video_player()` or `show_url()` on their own `GUIInterface` namespace when they take over rendering (e.g., a full-screen video overlay). This is separate from the OCP player chrome.
- `show_audio_player()` is now **deprecated for OCP use** — `show_media_player()` supersedes it for all media service callers. `show_audio_player()` remains valid for simple skills that play a single audio track without playlist/search UI needs.

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

### 6.2 GUI routing key

Every GUI event is tagged with a **routing key** computed by `_gui_routing_key(message)` from the message's session context (`message.context["session"]`). Adapters use this key to send only to the matching GUI clients.

Three cases, in priority order:

| Case | Condition | Routing key | Example |
|---|---|---|---|
| **On-device** | `session_id == "default"` | `"default"` | Mark2, laptop with local listener |
| **Location group** | `site_id` is set and not `"unknown"` | `site_id` value | `"living_room"` — mirrors to all screens at that location |
| **Standalone remote** | UUID `session_id`, no `site_id` | `session_id` | Phone GUI connected to a remote OVOS server |

GUI clients register with their routing key at connect time:
- Qt: `mycroft.gui.connected` → `"site_id"` field (defaults to `"default"`)
- Browser: `GET /?routing_key=<key>` (defaults to `"default"`)

**Routing rules:**
- Template events, session data → sent only to clients whose routing key matches
- Namespace removal, status events (wakeword, speaking, etc.) → broadcast to all connected clients

### 6.3 Template dispatch

`handle_show_page` is the central handler for `gui.page.show`. It checks the first page name:

- Starts with `"SYSTEM_"` → **template path**: dispatches to all adapters with the routing key, then activates the namespace on the internal stack. No legacy page-loading occurs.
- Otherwise → **legacy path**: activates namespace, loads pages into stack (unchanged behaviour).

```python
if page_ids_to_show and page_ids_to_show[0].startswith("SYSTEM_"):
    namespace = self._ensure_namespace_exists(namespace_name)
    data = {k: v for k, v in namespace.data.items()}
    routing_key = self._gui_routing_key(message)
    for template in page_ids_to_show:
        self._dispatch_template_to_adapters(template, namespace_name, data, routing_key)
    with namespace_lock:
        if not self.active_namespaces or self.active_namespaces[0].skill_id != namespace_name:
            self._activate_namespace(namespace_name, routing_key)
    return
```

### 6.4 Session data forwarding

Every `gui.value.set` message calls `adapter.on_session_update(skill_id, filtered_data, routing_key)` on all adapters after updating the internal namespace data. `__from` and `__idle` reserved keys are stripped before delivery.

### 6.5 Lifecycle hook invocation

| Internal event | Adapter hook called | Routing |
|---|---|---|
| Namespace moves to top of active stack | `on_namespace_activated(skill_id, routing_key)` | per-key |
| Namespace removed from active stack | `on_namespace_deactivated(skill_id)` | broadcast all |
| `gui.value.set` received | `on_session_update(skill_id, data, routing_key)` | per-key |
| Status event forwarded | `on_status_event(event_name, data)` | broadcast all |

Status events (wakeword, speaking, etc.) are broadcast to all clients — they are system-wide signals not tied to a specific session or location.

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
def handle_show_text(self, skill_id: str, data: dict, site_id: str = "default") -> None: ...
def handle_show_weather(self, skill_id: str, data: dict, site_id: str = "default") -> None: ...
# ... 19 others — see AbstractGUIPlugin._TEMPLATE_HANDLERS
```

`site_id` is the **routing key** computed from the message context (see §6.2). Adapters use it to deliver the update only to the matching client(s).

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
def on_namespace_activated(self, skill_id: str, site_id: str = "default") -> None: ...
def on_namespace_deactivated(self, skill_id: str) -> None: ...
def on_idle(self) -> None: ...
def on_session_update(self, skill_id: str, data: dict, site_id: str = "default") -> None: ...
def on_status_event(self, event_name: str, data: dict, site_id: str = "default") -> None: ...
```

`on_namespace_deactivated` and `on_status_event` are system-wide signals; although `site_id` is accepted for API consistency, adapters should broadcast these to all connected clients regardless of routing key.

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

**File:** `ovos_plugin_manager/gui_adapter.py`

```python
find_gui_adapter_plugins() -> Dict[str, Type[AbstractGUIPlugin]]
load_gui_adapter_plugin(module_name) -> Optional[Type[AbstractGUIPlugin]]

OVOSGUIAdapterFactory.create(module_name, config, bus) -> Optional[AbstractGUIPlugin]
OVOSGUIAdapterFactory.create_all(config, bus) -> List[AbstractGUIPlugin]
```

`GUIService._load_adapter_plugins()` calls `create_all` with:
- `config = mycroft.conf["gui"]["adapters"]`
- `bus = self.bus` (the shared MessageBusClient)

Plugins that raise during `__init__` are skipped and logged; they do not prevent other adapters from loading.

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
- For each `handle_show_*` call, resolves the matching bundled QML file from its `ui/` directory and sends `mycroft.gui.list.insert` + `mycroft.session.set` messages only to clients whose `site_id` matches the routing key via `send_to_clients_for_site(site_id, msg)`
- Status events and namespace removal are broadcast to **all** connected Qt clients via `send_to_all_clients(msg)` — these are system-wide signals
- Each Qt client announces its routing key in the `mycroft.gui.connected` handshake: `{"site_id": "default"}` for on-device, `{"site_id": "living_room"}` for a location group, or a UUID for a standalone remote GUI
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
- For each `handle_show_*` call, instantiates the matching `Page` subclass from `templates/__init__.py` and calls `GUIManager.show_template_page(..., site_id=site_id)`
- DOM updates are pushed only to browser tabs whose routing key matches `site_id` via per-session SSE queues; status events broadcast to all tabs
- Each browser tab gets a unique `session_id` (a random hex token) and a dedicated SSE endpoint `/updates/{session_id}`; tabs declare their routing key at `GET /?routing_key=`
- `Renderer._clients: Dict[str, str]` maps `session_id → routing_key`; `send(data, site_id=None)` delivers to matching sessions (`None` = broadcast all)
- Implements `any_client_connected()` by checking `global_renderer._clients`
- Touch events from `ConfirmPage` / `SelectPage` call back to OVOS via `self.bus.emit()`
- Tabs that stop sending pings are cleaned up after 30 s (`_check_disconnected` daemon thread)

**Server routes:**
| Route | Purpose |
|---|---|
| `GET /?routing_key=default` | Serve initial HTML; register browser tab with a routing key (default: `"default"`) |
| `GET /updates/{session_id}` | Per-tab SSE stream for DOM patch events |
| `GET /local-event/{id}` | HTMX local callback — returns HTML fragment |
| `POST /global-event/{id}` | HTMX global callback — no body returned |
| `POST /ping/{session_id}` | Browser keepalive; sessions without pings time out after 30 s |
| `GET /assets/*` | Static CSS/JS/font files |

**Routing key values (query parameter `routing_key`):**

| Value | Meaning |
|---|---|
| `"default"` | On-device display (Mark 2, laptop) — default if not specified |
| `"living_room"` / any string | Named physical location group |
| `"<uuid>"` | Standalone remote GUI (phone/tablet) — must match the OVOS session ID |

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
- [ ] `AbstractGUIPlugin` in `templates/gui.py` has all 22 `handle_show_*` methods (defaulting to no-op)
- [ ] `AbstractGUIPlugin._TEMPLATE_HANDLERS` maps all 22 `SYSTEM_*` strings to handler names
- [ ] `handle_show_media_player(self, skill_id, data, site_id="default")` exists (default no-op)
- [ ] `dispatch_template()` catches and logs exceptions without re-raising
- [ ] `on_namespace_activated`, `on_namespace_deactivated`, `on_idle`, `on_session_update`, `on_status_event` all exist (defaulting to no-op)
- [ ] `OVOSGUIAdapterFactory.create_all()` in `gui_adapter.py` loads all installed plugins
- [ ] Failed plugin instantiation is caught, logged, and skipped (other plugins continue)

### ovos-gui

- [ ] `ovos_gui/bus.py` does not exist (deleted — Tornado WS moved to legacy plugin)
- [ ] `NamespaceManager.__init__` does NOT call `create_gui_service()` or start any WS server
- [ ] `NamespaceManager` constructor accepts `adapters: list = None`
- [ ] `_gui_routing_key(message)` implements the three-case logic: `session_id=="default"` → `"default"`, `site_id` set and not `"unknown"` → `site_id`, else → `session_id`
- [ ] `handle_show_page` routes `SYSTEM_*` page names to `_dispatch_template_to_adapters(template, skill_id, data, routing_key)` and returns early (skips legacy path)
- [ ] `_dispatch_template_to_adapters` calls `adapter.dispatch_template(template, skill_id, data, site_id)` for each adapter
- [ ] `handle_set_value` calls `adapter.on_session_update(namespace_name, filtered_data, routing_key)` for each adapter (after stripping reserved keys)
- [ ] `_activate_namespace(namespace, routing_key)` calls `adapter.on_namespace_activated(skill_id, routing_key)` for each adapter
- [ ] `_remove_namespace` calls `adapter.on_namespace_deactivated(skill_id)` for each adapter (broadcast — no routing key)
- [ ] `handle_status_request` uses `adapter.any_client_connected()` (not a Tornado client list)
- [ ] Status events from `_define_messages_to_forward` call `adapter.on_status_event(event_name, data)` for each adapter (broadcast — no routing key)

### ovos-gui-api-client

- [ ] `GUIInterface` is the class exported from `ovos_gui_api_client`
- [ ] All 22 `show_*()` methods exist and set the correct session data keys before calling `_show_page(PageTemplates.SYSTEM_*)`
- [ ] `show_media_player(now_playing, playlist, search_results, state)` exists and writes all `ocp_*` session keys (see §4.3a)
- [ ] `PageTemplates.SYSTEM_media_player` constant exists
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
- [ ] `QtGUIWebSocketHandler` has `_site_id` attribute set from `mycroft.gui.connected` handshake (`site_id` field, default `"default"`)
- [ ] `send_to_clients_for_site(site_id, msg)` delivers only to clients where `client.site_id == site_id` (exact match — `"default"` is NOT a wildcard)
- [ ] `send_to_all_clients(msg)` used for status events and namespace removal (system-wide)
- [ ] All 21 `handle_show_*` methods have signature `(self, skill_id, data, site_id="default")` and use `send_to_clients_for_site`
- [ ] `on_namespace_activated(skill_id, site_id="default")` uses `send_to_clients_for_site`
- [ ] `on_namespace_deactivated(skill_id)` uses `send_to_all_clients`
- [ ] `on_status_event(event_name, data, site_id="default")` uses `send_to_all_clients` (always broadcast)
- [ ] All 21 `handle_show_*` methods implemented; each resolves a bundled QML file from `ui/`
- [ ] Skills supply no QML — all 21 QML stubs are bundled inside this plugin's `ui/` directory
- [ ] Implements `any_client_connected()` based on active WS connections

### ovos-gui-plugin-pyhtmx

- [ ] Inherits from `AbstractGUIPlugin`
- [ ] Registered under entry point group `opm.gui_adapter` as `pyhtmx_gui:PyHTMXGUIPlugin`
- [ ] Starts FastAPI/uvicorn in a daemon thread in `__init__`
- [ ] `app.py` has NO `/cache` static mount
- [ ] `gui_client.py` does not exist (deleted)
- [ ] `GET /` accepts `routing_key: str = "default"` query parameter; generates a per-tab `session_id`; patches `sse-connect` to `/updates/{session_id}` and ping URL to `/ping/{session_id}`
- [ ] `GET /updates/{session_id}` serves a dedicated SSE queue per browser tab
- [ ] `EventSender` uses `{session_id: Queue}` dict; `send(msg, session_ids=None)` delivers to matching tabs (`None` = broadcast all)
- [ ] `Renderer._clients: Dict[str, str]` maps `session_id → routing_key`; `register_client(session_id, routing_key)` populates it
- [ ] `Renderer.send(data, site_id=None)` — `None` broadcasts; string routes to matching sessions only
- [ ] `_check_disconnected` daemon cleans up sessions that stop pinging after 30 s
- [ ] All 21 `handle_show_*` methods have signature `(self, skill_id, data, site_id="default")`; pass `site_id` to `show_template_page`
- [ ] `on_namespace_activated(skill_id, site_id="default")` passes `site_id` to `GUIManager.show`
- [ ] `on_status_event(event_name, data, site_id="default")` passes `site_id=None` to `GUIManager.update_status` (always broadcast)
- [ ] `templates/__init__.py` defines all 21 `Page` subclasses and `TEMPLATE_PAGE_MAP`
- [ ] `ConfirmPage` and `SelectPage` accept `skill_id` and call back to OVOS bus on touch
- [ ] `app.set_plugin(plugin)` must be called before uvicorn starts
- [ ] Implements `any_client_connected(site_id=None)` via `global_renderer._clients`
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

    def handle_show_text(self, skill_id: str, data: dict, site_id: str = "default") -> None:
        # site_id is the routing key — use it to target specific terminals if applicable
        print(f"[{skill_id}@{site_id}] {data.get('title', '')}: {data.get('text', '')}")

    def handle_show_weather(self, skill_id: str, data: dict, site_id: str = "default") -> None:
        print(f"[{skill_id}@{site_id}] {data['location']}: {data['current_temp']}° {data['condition']}")

    def on_status_event(self, event_name: str, data: dict, site_id: str = "default") -> None:
        # Status events are system-wide — ignore site_id and broadcast to all terminals
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
