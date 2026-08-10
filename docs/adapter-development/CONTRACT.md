# Adapter Interface Contract

The binding contract a GUI adapter (`opm.gui_adapter` plugin) must honor to work
with ovos-gui. Adapters subclass
`ovos_plugin_manager.templates.gui.AbstractGUIPlugin`.

Routing is keyed solely by `session_id`. A shared/multi-room screen is expressed
by clients sharing the same `session_id`; the on-device default is
`session_id == "default"`. There is no `site_id` and no separate `routing_key`.

## Construction

```python
def __init__(self, config: dict, bus: MessageBusClient | None = None):
    super().__init__(config, bus)
```

- `config` — the adapter section from `mycroft.conf → gui.adapters.<entry-point-name>`. May be empty.
- `bus` — the shared OVOS `MessageBusClient`. May be `None` in tests. Use it via `self.bus`.

Initialize only lightweight resources and return quickly: adapters load at GUI
startup, so a slow `__init__` blocks the service. Start servers/render pipelines
on a daemon thread.

## Template handlers

```python
def handle_show_weather(self, skill_id: str, data: dict, session_id: str = "default") -> None: ...
```

- `skill_id` — the namespace that requested the display.
- `data` — the full session-data dict for that namespace at call time (reserved keys `__from`/`__idle` already stripped).
- `session_id` — the target session; deliver only to clients on that session.

Override only the handlers you support; all default to no-ops. The full mapping
of `SYSTEM_*` template names to handler methods is
`AbstractGUIPlugin._TEMPLATE_HANDLERS`; dispatch goes through
`dispatch_template(template, skill_id, data, session_id)`, which catches and
logs exceptions.

## Lifecycle hooks

```python
def on_namespace_activated(self, skill_id: str, session_id: str = "default") -> None: ...
def on_namespace_deactivated(self, skill_id: str, session_id: str = "default") -> None: ...
def on_idle(self) -> None: ...
def on_session_update(self, skill_id: str, data: dict, session_id: str = "default") -> None: ...
def on_status_event(self, event_name: str, data: dict, session_id: str = "default") -> None: ...
```

`on_status_event` carries system-wide signals (e.g. `recognizer_loop:wakeword`,
`speak`); broadcast these to all clients regardless of `session_id`.

## Connection status

```python
def any_client_connected(self) -> bool: ...
```

Return `True` when at least one client is connected. ovos-gui answers
`gui.status.request` with `True` if any adapter reports a connected client.

## Behavioral requirements

- **Exception-safe.** Never let an exception escape a handler or hook; catch and
  log. ovos-gui wraps calls defensively, but adapters must not rely on it.
- **Non-blocking.** Adapters are called sequentially on the caller's thread. Do
  blocking I/O (network, disk, sleep) on a background thread.
- **No shared state mutation.** Do not modify `NamespaceManager` state. Keep only
  your own per-`session_id`/per-`skill_id` state and clean it up on
  `on_namespace_deactivated`. Do not cache the `data` dict; re-read fresh state
  via the query API when needed later.

## State query API

ovos-gui exposes read-only queries on `NamespaceManager` for crash recovery:

```python
get_active_namespace(session_id="default") -> Namespace | None
get_namespace_data(namespace_name, session_id="default") -> dict | None  # a copy
get_all_sessions() -> list[str]
is_namespace_active(namespace_name, session_id="default") -> bool
```

Use sparingly and handle `None` (the namespace may have been removed).

## Registration

```toml
# pyproject.toml
[project.entry-points."opm.gui_adapter"]
"my-adapter" = "my_package:MyAdapterClass"
```

`ovos-gui` discovers and loads every installed `opm.gui_adapter` plugin at
startup via `OVOSGUIAdapterFactory.create_all(bus=..., config=...)` and dispatches
every template event to all of them (multi-modal by default). A device with no
adapters installed runs headless: dispatch is a silent no-op.

## Minimal adapter

```python
from ovos_plugin_manager.templates.gui import AbstractGUIPlugin


class TerminalGUIPlugin(AbstractGUIPlugin):
    def handle_show_text(self, skill_id, data, session_id="default"):
        print(f"[{skill_id}@{session_id}] "
              f"{data.get('title', '')}: {data.get('text', '')}")

    def on_status_event(self, event_name, data, session_id="default"):
        print(f"[status] {event_name}")  # broadcast; ignore session_id

    def any_client_connected(self) -> bool:
        return True
```
