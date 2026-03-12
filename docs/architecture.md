# Architecture Overview

## Motivation

The original OVOS/Mycroft GUI system required every skill to ship framework-specific
rendering assets:

- **Qt skills** — `.qml` files in `gui/qt5/` and `gui/qt6/`
- **pyhtmx skills** — `.py` page classes in `gui/py-htmx/`

This created several problems:

- Skills were tightly coupled to a specific display technology.
- Adding a new display backend (terminal UI, web browser, e-ink, etc.) required
  modifying every existing skill.
- Skills that only supported one framework silently showed nothing on devices
  running a different one.
- The `ovos-gui` service embedded the Tornado WebSocket server directly, making
  it impossible to replace without patching the service itself.

## Design

The refactor introduces two orthogonal abstractions:

1. **Template-based `GUIInterface`** (`ovos-gui-api-client`) — skills call typed
   methods (`show_weather()`, `show_text()`, …) instead of naming framework files.
   The interface emits `gui.page.show` messages where `page_names` contains a
   `SYSTEM_*` identifier drawn from the `PageTemplates` enum.

2. **GUI adapter plugin system** (`opm.gui_adapter` entry point) — rendering is
   done by independently installable plugins that subscribe to `AbstractGUIPlugin`
   callbacks.  All loaded adapters receive every template event simultaneously,
   enabling multi-modal output (Qt window + browser + terminal at once).

## Component diagram

```
┌──────────────────────────────────────────────────────────┐
│  Skill (OVOSSkill)                                       │
│                                                          │
│  self.gui.show_weather(22, 18, 26, "Sunny", ...)         │
└────────────────────┬─────────────────────────────────────┘
                     │  gui.value.set  +  gui.page.show
                     │  (MessageBus)
                     ▼
┌──────────────────────────────────────────────────────────┐
│  ovos-gui  —  NamespaceManager                           │
│                                                          │
│  Detects SYSTEM_* in page_names                          │
│  → calls adapter.dispatch_template() on all adapters     │
│  Detects non-SYSTEM_* → legacy path (unchanged)          │
└──────┬───────────────────────────┬───────────────────────┘
       │                           │
       ▼                           ▼
┌─────────────────┐   ┌────────────────────────────────────┐
│ LegacyMycoft    │   │  Any other opm.gui_adapter plugin  │
│ GuiPlugin       │   │  (pyhtmx, TUI, e-ink, …)           │
│                 │   │                                    │
│ Tornado WS      │   │  Implements handle_show_weather()  │
│ server          │   │  however it sees fit               │
│ port 18181      │   └────────────────────────────────────┘
│                 │
│ mycroft.session │
│ .set / list.*   │
│ / gui.list.*    │
│                 │
└────────┬────────┘
         │  WebSocket
         ▼
   Qt5 / Qt6 GUI client
   (mycroft-gui)
   renders bundled QML
```

## Package responsibilities

| Package | Role |
|---|---|
| `ovos-gui-api-client` | `GUIInterface` with 21 typed `show_*()` methods; `PageTemplates` enum; `FillMode`, `ListItem`, `GridItem`, `SelectItem` data types |
| `ovos-workshop` | `OVOSSkill.gui` returns a `GUIInterface` (now sourced from `ovos-gui-api-client`) |
| `ovos-plugin-manager` | `AbstractGUIPlugin` base class; `PluginTypes.GUI_ADAPTER`; `OVOSGUIAdapterFactory` |
| `ovos-gui` | `NamespaceManager` routes SYSTEM_* template events to all loaded adapters; starts adapters at service startup |
| `ovos-legacy-mycroft-gui-plugin` | Adapter that translates templates to the mycroft-gui Qt WebSocket protocol; bundles all 21 QML pages |

## Data flow for a single `show_weather()` call

```
skill.gui.show_weather(22, 18, 26, "Sunny")
│
├─ gui["current_temp"] = 22   ─┐
├─ gui["min_temp"]     = 18    │  GUIInterface.__setitem__
├─ gui["max_temp"]     = 26    │  (queued, no bus emit yet)
├─ gui["condition"]    = "Sunny" ┘
│
├─ GUIInterface._show_pages(["SYSTEM_weather"])
│    ├─ bus.emit("gui.value.set", {current_temp, min_temp, ...})
│    └─ bus.emit("gui.page.show", {page_names: ["SYSTEM_weather"], ...})
│
└─ NamespaceManager.handle_show_page()
     ├─ page_names[0].startswith("SYSTEM_")  →  True
     ├─ read namespace.data  (updated by handle_set_value just before)
     └─ for adapter in self.adapters:
          adapter.dispatch_template("SYSTEM_weather", skill_id, data)
            └─ adapter.handle_show_weather(skill_id, data)
```

## Backward compatibility

- Non-SYSTEM_* page names in `gui.page.show` go through the unchanged legacy
  namespace management path inside `NamespaceManager`.
- The `LegacyMycoftGuiPlugin` intercepts template events and translates them to
  Qt WebSocket messages, so existing Qt deployments continue working without
  modification.
- Headless deployments (no adapter installed) — all `GUIInterface` calls are
  silently no-ops because the bus `gui.page.show` message is emitted but
  `NamespaceManager.adapters` is empty.
