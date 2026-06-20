# ovos-gui Architecture

ovos-gui is the GUI **state and dispatch hub**. It runs no display backend and no
WebSocket server. Skills declare *what* to show via semantic templates; ovos-gui
fans every template event out to all installed adapter plugins, which render it
on their respective surfaces (Qt, browser, terminal, ...).

```
Skill (ovos-gui-api-client GUIInterface)
  │  gui.value.set / gui.page.show(SYSTEM_*)   [MessageBus]
  ▼
ovos-gui / NamespaceManager
  • per-session LIFO namespace stack
  • dispatches SYSTEM_* templates to every adapter (session_id-routed)
  │  dispatch_template(...) to each adapter
  ├── ovos-legacy-mycroft-gui-plugin   (Tornado WS -> Qt/QML)
  └── ovos-gui-plugin-pyhtmx           (FastAPI/SSE -> browser)
```

## Components

- **`GUIService`** (`ovos_gui/service.py`) — connects to the bus and loads
  adapters via `OVOSGUIAdapterFactory.create_all(bus, config)`. Zero adapters is
  a valid headless state (no-op dispatch), never an error.
- **`NamespaceManager`** (`ovos_gui/namespace.py`) — owns the active-namespace
  stack per `session_id`, parses persistence (`__idle`), schedules timed
  removals, and invokes adapter handlers/hooks. Exposes the read-only state
  query API for adapters.
- **`AbstractGUIPlugin`** (`ovos_plugin_manager.templates.gui`) — the adapter
  base class and `opm.gui_adapter` entry-point contract. See
  [CONTRACT.md](CONTRACT.md).

## Routing

The sole routing key is `session_id`
(`message.context["session"]["session_id"]`, default `"default"`). Each
`session_id` has an independent namespace stack. Clients that should mirror the
same content share a `session_id`. Template events and session-data updates are
routed by `session_id`; status events are broadcast to all clients.

## Invariants

1. ovos-gui runs no WebSocket server; transports live entirely in adapters.
2. With no adapter installed, every dispatch is a silent no-op — skills never
   crash on headless devices.
3. A failing adapter is isolated (logged) and never blocks other adapters or the
   service.
4. All display goes through `SYSTEM_*` templates; custom QML page names are
   rejected.
