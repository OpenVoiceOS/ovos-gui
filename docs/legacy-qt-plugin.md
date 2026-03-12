# Legacy Qt GUI Plugin

**Package:** `ovos-legacy-mycroft-gui-plugin`
**Entry point:** `opm.gui_adapter = ovos_legacy_mycroft_gui:LegacyMycoftGuiPlugin`

This adapter translates the new OVOS template API (`SYSTEM_*` page identifiers) into the
mycroft-gui Qt WebSocket protocol so existing Qt5/Qt6 GUI clients can display skill output
without any skill-provided QML files.

All rendering is done by the 21 system-template QML pages bundled in `mycroft-gui-qt5`
and installed to `$prefix/share/mycroft-gui/system-templates/`.  The plugin sends
`SYSTEM:<Name>.qml` URIs over the wire; the Qt client resolves them to local files.
Skills no longer ship any `gui/qt5/` or `gui/qt6/` directories.

This adapter also includes a **HomescreenManager** that handles all idle-screen data
(date/time, weather, wallpaper, notifications, apps, examples, widgets) and re-emits it
as `homescreen.data.*` / `homescreen.widget.*` bus events consumed by the Qt shell
(e.g. `ovos-shell`). `ovos-skill-homescreen` is deprecated; the homescreen is now a
built-in responsibility of the shell and this adapter plugin.

---

## Architecture

```
NamespaceManager
      │
      │  dispatch_template("SYSTEM_weather", skill_id, data)
      ▼
LegacyMycoftGuiPlugin
      │
      ├─ _sync_session_data()   →  mycroft.session.set   (WS)
      ├─ _push_namespace()      →  mycroft.session.list.insert / list.move  (WS)
      └─ _show_qml()            →  mycroft.gui.list.insert
                                   mycroft.events.triggered (page_gained_focus)  (WS)
      │
      ▼
  Qt5 / Qt6 mycroft-gui client
  renders bundled Weather.qml, Text.qml, etc.
```

---

## Startup

`LegacyMycoftGuiPlugin.__init__` performs two actions:

1. **Starts the Tornado WebSocket server** on the port defined in config
   (default `18181`) via `create_gui_service(self)`.

2. **Registers** `mycroft.gui.connected` on the OVOS core bus so Qt clients
   receive the WebSocket port when they announce themselves.

3. **Starts `HomescreenManager`** which subscribes to datetime, weather, wallpaper,
   notification, app, widget and connectivity events and re-emits them as
   `homescreen.data.*` / `homescreen.widget.*` messages for the shell homescreen.

```python
plugin = LegacyMycoftGuiPlugin(config={"default_qt_version": 5}, bus=bus)
# → WebSocket server listening on port 18181
```

---

## Template → QML mapping

Every `SYSTEM_*` template identifier is mapped to a bundled QML file:

| Template identifier | QML file |
|---|---|
| `SYSTEM_idle` | `Idle.qml` |
| `SYSTEM_loading` | `Loading.qml` |
| `SYSTEM_status` | `Status.qml` |
| `SYSTEM_error` | `Error.qml` |
| `SYSTEM_text` | `Text.qml` |
| `SYSTEM_image` | `Image.qml` |
| `SYSTEM_animated_image` | `AnimatedImage.qml` |
| `SYSTEM_list` | `List.qml` |
| `SYSTEM_grid` | `Grid.qml` |
| `SYSTEM_table` | `Table.qml` |
| `SYSTEM_html` | `Html.qml` |
| `SYSTEM_url` | `Url.qml` |
| `SYSTEM_audio_player` | `AudioPlayer.qml` |
| `SYSTEM_video_player` | `VideoPlayer.qml` |
| `SYSTEM_clock` | `Clock.qml` |
| `SYSTEM_timer` | `Timer.qml` |
| `SYSTEM_weather` | `Weather.qml` |
| `SYSTEM_map` | `Map.qml` |
| `SYSTEM_confirm` | `Confirm.qml` |
| `SYSTEM_select` | `Select.qml` |
| `SYSTEM_face` | `Face.qml` |

QML files live under `ovos_legacy_mycroft_gui/ui/` inside the installed package.
`GuiPage.get_uri()` returns `file:///path/to/ui/Weather.qml`.

---

## `_show_template()` flow

Called for every template event received via `AbstractGUIPlugin`:

```python
def _show_template(self, template_id, skill_id, data):
    qml_name = _TEMPLATE_QML[template_id]      # e.g. "Weather.qml"
    ns = self._ensure_namespace(skill_id)
    ns.data.update(...)                         # merge session data

    self._sync_session_data(skill_id, ns.data)  # → mycroft.session.set
    self._push_namespace(skill_id)              # → mycroft.session.list.insert / move
    self._show_qml(skill_id, qml_name)          # → mycroft.gui.list.insert
                                                #   mycroft.events.triggered
```

---

## Qt WebSocket protocol messages

All messages are JSON objects sent over the WebSocket connection at `ws://localhost:18181`.

### Namespace stack management

**Insert namespace** (skill becomes visible):
```json
{
  "type": "mycroft.session.list.insert",
  "namespace": "mycroft.system.active_skills",
  "position": 0,
  "data": [{"skill_id": "ovos-skill-weather"}]
}
```

**Move namespace** (existing skill re-activated):
```json
{
  "type": "mycroft.session.list.move",
  "namespace": "mycroft.system.active_skills",
  "from": 2,
  "to": 0,
  "items_number": 1
}
```

**Remove namespace** (skill cleared / idle):
```json
{
  "type": "mycroft.session.list.remove",
  "namespace": "mycroft.system.active_skills",
  "position": 0,
  "items_number": 1
}
```

### Session data sync

Sent once per key before showing a page:
```json
{
  "type": "mycroft.session.set",
  "namespace": "ovos-skill-weather",
  "data": {"current_temp": 22}
}
```

### Page display

Insert the QML page at position 0.  The `url` field uses the `SYSTEM:` URI scheme;
the Qt client resolves it to the local `system-templates/` directory:
```json
{
  "type": "mycroft.gui.list.insert",
  "namespace": "ovos-skill-weather",
  "position": 0,
  "data": [{"url": "SYSTEM:Weather.qml", "page": "Weather.qml"}]
}
```

Focus the page:
```json
{
  "type": "mycroft.events.triggered",
  "namespace": "ovos-skill-weather",
  "event_name": "page_gained_focus",
  "data": {"number": 0}
}
```

### Status events

System events from the OVOS core bus are forwarded as:
```json
{
  "type": "mycroft.events.triggered",
  "namespace": "system",
  "event_name": "recognizer_loop:wakeword",
  "data": {}
}
```

---

## New client synchronization

When a Qt client connects via WebSocket, `QtGUIWebSocketHandler.open()` calls
`plugin.synchronize(client)`. This replays the full current state to the new client:

1. Re-sends `mycroft.session.list.insert` for every namespace in `_active_stack` (in order).
2. For each namespace, re-sends `mycroft.gui.list.insert` with its current QML page.
3. Re-sends all `mycroft.session.set` messages for every key in `namespace.data`.

This ensures a Qt client that connects after skill output has already been shown
still receives a complete, up-to-date display state.

---

## Qt client → OVOS core bus

Messages received from Qt clients over the WebSocket are forwarded to the OVOS
core bus unchanged. This allows Qt GUI interactions (button presses, text input)
to reach skills as normal bus events.

---

## Configuration

```json
{
  "gui": {
    "adapters": {
      "ovos-legacy-mycroft-gui": {
        "base_port": 18181,
        "default_qt_version": 5
      }
    }
  }
}
```

| Key | Default | Description |
|---|---|---|
| `base_port` | `18181` | TCP port the Tornado WebSocket server listens on |
| `default_qt_version` | `5` | Used when a Qt client does not declare its framework version |

---

## System template QML files

The 21 system-template QML pages are **not** bundled with this plugin.  They live in
`mycroft-gui-qt5` under `import/system-templates/` and are installed to
`$prefix/share/mycroft-gui/system-templates/`.

`GuiPage.get_uri()` returns `"SYSTEM:<Name>.qml"`.  The Qt client's `resolveDelegate()`
intercepts `SYSTEM:` URIs and maps them to local files:

1. `$OVOS_SYSTEM_TEMPLATES/<Name>.qml` — if the env var is set **and** the file exists
2. `$MYCROFT_SYSTEM_TEMPLATES_DIR/<Name>.qml` — compiled-in default (`/usr/share/mycroft-gui/system-templates/`)

Shell applications (e.g. `ovos-shell`) can override individual templates by setting
`OVOS_SYSTEM_TEMPLATES` to a sparse directory that contains only the overridden files.

See `mycroft-gui-qt5/documentation/system-templates.md` for the full template
inventory and session data key reference.

---

## HomescreenManager

`HomescreenManager` runs as part of the plugin (started in `LegacyMycoftGuiPlugin.__init__`).
It replaces `ovos-skill-homescreen`, which is now deprecated.

It subscribes to homescreen data sources on the OVOS bus and re-emits structured events
that the Qt shell (`ovos-shell`) consumes via `HomescreenController.qml`:

| Event emitted | Payload keys | Source |
|---|---|---|
| `homescreen.data.time` | `time_string`, `date_string`, `weekday_string`, `day_string`, `month_string`, `year_string` | `ovos_date_parser` (every 10 s) |
| `homescreen.data.weather` | `weather_api_enabled`, `weather_code`, `weather_temp` | `skill-ovos-weather.openvoiceos.weather.response` |
| `homescreen.data.wallpaper` | `wallpaper_path`, `selected_wallpaper` | `homescreen.wallpaper.set` |
| `homescreen.data.notifications` | `notification_counter`, `notification_model` | `ovos.notification.update_*` |
| `homescreen.data.apps` | `applications_model` | `homescreen.register.app` / `detach_skill` |
| `homescreen.data.examples` | `skill_examples`, `skill_info_enabled`, `skill_info_prefix` | `homescreen.register.examples` / config |
| `homescreen.data.connectivity` | `system_connectivity` | `mycroft.network.connected` etc. |
| `homescreen.widget.timer` | `count`, widget fields | `ovos.widgets.timer.*` |
| `homescreen.widget.alarm` | `count`, widget fields | `ovos.widgets.alarm.*` |
| `homescreen.widget.media` | `enabled`, `widget`, `state` | OCP player state + track info |

The shell's `HomescreenController.qml` subscribes to all these events and exposes the
data as plain QML properties that `idle.qml` and its sub-components bind to directly.
