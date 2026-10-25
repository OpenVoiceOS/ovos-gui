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
`dispatch_template(template, skill_id, data, session_id, index=0, page_count=1)`,
which catches and
logs exceptions. It includes the interactive companions `SYSTEM_confirm`,
`SYSTEM_select` and `SYSTEM_input` of the proposed amendment A.

ovos-gui decides "template or legacy page" on the **first** `page_names` entry
([4.2](https://github.com/OpenVoiceOS/architecture/blob/b6c1583/gui-1.md#42-messages)) and dispatches only the
**active** entry (`index`). A list that mixes `SYSTEM_*` and other names gets one
diagnostic.

## Active entry: `index` and `page_count`

ovos-gui passes two keyword arguments to `dispatch_template` and `on_legacy_page`, as
[6.3](https://github.com/OpenVoiceOS/architecture/blob/b6c1583/gui-1.md#63-events-received) (proposed amendment B) defines them:

- `index`: the active entry's zero-based position in `page_names` (after clamping).
- `page_count`: the length of `page_names`.

They come on every show, and again on the dispatch after a valid `gui.page.focus`
(below). That second dispatch, with the new `index`, is how a client learns that the
focus took effect. A client that has not received both values for a namespace must not
send `gui.page.focus` for it.

ovos-gui inspects the hook's signature. A hook that has no `index` and `page_count`
parameters (and no `**kwargs`) is called without them, and ovos-gui logs this once per
adapter class and hook. An adapter written before these arguments therefore keeps working.

## Legacy page hook

```python
def on_legacy_page(self, skill_id: str, page: str, data: dict, session_id: str = "default",
                   index: int = 0, page_count: int = 1) -> None: ...
```

When the first `page_names` entry is not a `SYSTEM_*` name, ovos-gui never
dispatches the show as a template. It calls this hook with the active entry
instead, in the template order: `on_session_update`, `on_legacy_page`,
`on_namespace_activated`. This is the optional, transitional legacy-page hook of
the proposed amendment E. An adapter that cannot draw skill pages ignores it.

## Lifecycle hooks

```python
def on_namespace_activated(self, skill_id: str, session_id: str = "default") -> None: ...
def on_namespace_deactivated(self, skill_id: str, session_id: str = "default") -> None: ...
def on_idle(self, session_id: str = "default") -> None: ...
def on_session_update(self, skill_id: str, data: dict, session_id: str = "default") -> None: ...
def on_status_event(self, event_name: str, data: dict, session_id: str = "default") -> None: ...
```

`on_idle` names the session whose stack just emptied, and is called only then.
Idle is per session: show the resting display to the clients of that session only.

`on_status_event` carries the status signals of
[5.3](https://github.com/OpenVoiceOS/architecture/blob/b6c1583/gui-1.md#53-system-wide-signals) (e.g.
`ovos.listener.wakeword`, `ovos.utterance.speak`), the `gui.ambient.*` topics of
[6.9.1](https://github.com/OpenVoiceOS/architecture/blob/b6c1583/gui-1.md#691-ambient-data) and the legacy topics ovos-gui
still forwards; broadcast these to all clients regardless of `session_id`.

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
  `on_namespace_deactivated`. Do not cache the `data` dict longer than you
  need it. (The query API below cannot be reached from an adapter yet, so an
  adapter that serves late clients keeps its own copy for now.)

## Events from clients

An adapter whose clients send events puts them on `self.bus`, with the client's
session in `context["session"]["session_id"]`. ovos-gui handles:

- `gui.page.focus` `{namespace, page_number}` (proposed amendment B): for the
  namespace on top of that session's stack and an in-range entry, ovos-gui makes
  the entry active and dispatches it again (a template or `on_legacy_page`), with
  the new `index`. It
  also restarts the namespace's removal timer. A request that names the current
  entry only restarts the timer. Any other request is ignored with one diagnostic.
- `gui.interaction` `{namespace, event, data}` (proposed amendment A) is for the
  application; ovos-gui does not consume it.

## State query API

ovos-gui has read-only queries on `NamespaceManager`
([6.7](https://github.com/OpenVoiceOS/architecture/blob/b6c1583/gui-1.md#67-state-query-recovery)):

```python
get_active_namespace(session_id="default") -> Namespace | None
get_namespace_data(namespace_name, session_id="default") -> dict | None  # a copy
get_all_sessions() -> list[str]
is_namespace_active(namespace_name, session_id="default") -> bool
get_ambient(topic) -> dict | None  # last gui.ambient.* payload, a copy
```

An adapter is constructed with only `(config, bus)`, so today it has **no handle**
to this surface (review C9, PHASE1 P6). The queries serve ovos-gui itself and its
tests until the spec defines how an adapter reaches them. Handle `None` (the
namespace may have been removed).

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
