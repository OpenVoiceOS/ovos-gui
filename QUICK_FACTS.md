
# Quick Facts — `ovos-gui`

GUI service daemon for Open Voice Operating System (OVOS). Manages namespace-based rendering, adapter plugins, and GUI communication.

| Feature | Details |
|---------|---------|
| **Package Name** | `ovos-gui` |
| **Current Version** | `1.3.5a3` |
| **License** | Apache-2.0 |
| **Repository** | [OpenVoiceOS/ovos-gui](https://github.com/OpenVoiceOS/ovos-gui) |
| **Python Support** | 3.10, 3.11, 3.12, 3.13 |
| **Primary Branch** | `dev` |
| **Release Branch** | `master` |

## Key Metrics (2026-03-12)

| Metric | Value |
|--------|-------|
| **Test Coverage** | 88% (131 tests) |
| **Lines of Code** | ~2,200 |
| **Documentation Files** | 7 (in docs/) |
| **Entry Points** | 2 |
| **Dependencies** | 4 core (ovos-utils, ovos-plugin-manager, ovos-bus-client, ovos-config) |

## Core Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `GUIService` | `ovos_gui.service` | Main service daemon |
| `NamespaceManager` | `ovos_gui.namespace` | Manages GUI namespaces and page state |
| `Namespace` | `ovos_gui.namespace` | Individual GUI namespace |
| `GuiPage` | `ovos_gui.page` | Single GUI page descriptor |
| `GUIDebugger` | `ovos_gui.tui` | Terminal UI debugger for testing |

## Entry Points

### CLI Scripts
- **`ovos-gui-service`** → `ovos_gui.__main__:main`
  - Starts the GUI service daemon
  - Usage: `ovos-gui-service`

- **`ovos-gui-debug-tui`** → `ovos_gui.tui:main`
  - Terminal debugger for real-time GUI inspection
  - Usage: `ovos-gui-debug-tui`

## OPM Plugin Type

This repo provides the core GUI service, not plugins. It loads adapter plugins:
- Entry point group: `opm.gui_adapter`
- Examples: `ovos-legacy-mycroft-gui-plugin` (Qt5), `ovos-gui-plugin-web` (browser)

## Recent Changes

**Phase 1-3 Completion (2026-03-12)**:
- ✅ 88% code coverage (55 new tests added)
- ✅ CI matrix fixed (Python 3.10-3.13, pinned actions)
- ✅ Qt5→Qt6 migration research and strategy documented
- ✅ 4 new research documents created
- ✅ Root documentation updated (FAQ, MAINTENANCE_REPORT, AUDIT)

See `MAINTENANCE_REPORT.md` for full change history.

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/index.md` | Documentation index |
| `docs/architecture.md` | System design and namespace architecture |
| `docs/templates.md` | GUI template API reference (21 methods) |
| `docs/adapter-plugins.md` | Plugin system specification |
| `docs/bus-protocol.md` | MessageBus protocol details |
| `docs/skill-migration.md` | Migrating skills to new GUI interface |
| `docs/legacy-qt-plugin.md` | Qt5 plugin implementation details |

## Known Limitations

See `AUDIT.md` for:
- Technical debt items
- Test coverage gaps (12% uncovered)
- Potential improvements

## Qt6 Status

**Not yet implemented** — See `QT6_ROLLOUT_STRATEGY.md`:
- Current: Qt5 support only via `ovos-legacy-mycroft-gui-plugin`
- Planned: Phased rollout with separate Qt6 adapter (v2.0)
- Timeline: 24-30 months for full Qt6 cutover

Research documents:
- `RESEARCH_Qt5_Qt6_MIGRATION.md` — API differences
- `ADAPTER_COMPATIBILITY_ASSESSMENT.md` — Technical assessment

