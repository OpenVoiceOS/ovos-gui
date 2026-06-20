# ovos-gui — agent guide

GUI messagebus service daemon for OpenVoiceOS. Manages GUI state (a LIFO stack of skill namespaces and their template pages) and exposes the standardized GUI template protocol over a websocket. GUI client/adapter plugins (Qt, web, shell-companion, etc.) connect to it to receive data and render it.

This is the daemon, not a GUI client and not a renderer. It owns protocol/state only.

## Setup

```bash
pip install -e .
# optional shell-companion extension:
pip install -e .[extras]
```

WARNING: `pyproject.toml` currently pins two dependencies to absolute local `file:///home/miro/...` paths (`ovos-plugin-manager` and `ovos-legacy-mycroft-gui-plugin`). A plain `pip install .` will fail on any other machine. Use the PyPI specs from `requirements/` (`ovos-plugin-manager>=0.5.5,<3.0.0`) when fixing packaging.

## Test

```bash
pip install -r test/requirements.txt   # pytest, pytest-cov
pytest test/unittests
```

End-to-end adapter integration tests live in `test/end2end/`.
Coverage (mirrors CI): `pytest --cov=ovos_gui --cov-report xml test/unittests`

## Lint/Typecheck

None configured.

## Layout

- `ovos_gui/service.py` — `GUIService`: bootstraps the bus client, loads `opm.gui_adapter` plugins via `OVOSGuiFactory.create_all`, owns process status. Entry point `ovos-gui-service`.
- `ovos_gui/namespace.py` — `NamespaceManager`: the core state engine. Maintains the active namespace stack, page persistence/timeouts, session data, and emits namespace/page bus events.
- `ovos_gui/page.py` — page model.
- `ovos_gui/message_types.py` — `GUIMessageType` str-enum: the full protocol vocabulary (connection, namespace, page, session, shell features, status events, legacy aliases).
- `ovos_gui/__main__.py` — `main()`; entry point `ovos-gui-service`.
- `ovos_gui/tui.py` — debug terminal UI client; entry point `ovos-gui-debug-tui`. Marked deprecated (move to legacy plugin repo).
- `ovos_gui/version.py` — version (managed by automation, do not edit).
- `ovos_qt_gui_plugin/` — empty directory (scaffold, no code).

No OPM/skill entry points are declared by this package; it is a `console_scripts` service that *consumes* `opm.gui_adapter` plugins.

## Conventions (Org hard rules)

- Branches: work on `dev`, stable is `master`. NEVER use `main`.
- Never edit `ovos_gui/version.py`; gh-automations bumps semver from conventional-commit prefixes (`feat:`/`fix:`/`feat!:`).
- New repos private by default.
- Commit identity: JarbasAi <jarbasai@mailfence.com>.
- Reference `OpenVoiceOS/gh-automations` reusable workflows at `@dev`.
- No Neon / `neon-*` references.
- No meta-commentary (no history, dates, or "design mistake" narration) in code, docs, commits, or PRs — describe current state only.
- CI is provided by OpenVoiceOS/gh-automations.

## Gotchas

- `pyproject.toml` has machine-local `file:///` dependency paths (see Setup) — top fix-it item.
- Committed scratch artifacts in the tree: `.coverage`, `htmlcov/`, `ovos_gui.egg-info/`, `.idea/`. None belong in git.
- GUI resource files are written to `~/.cache/mycroft/ovos-gui` by skills; clients on other machines/containers must share that volume — the service does not serve files.
- `message_types.py` carries both current and deprecated (`mycroft.*`) message aliases; check both when matching handlers.
- QML module versioning is inconsistent across consumers (issue #71); QT6 support is partial (issue #17).
