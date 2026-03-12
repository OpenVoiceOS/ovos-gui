# GUI Adapter Plugins

GUI adapter plugins are the rendering backends of the OVOS GUI system.
Any number can be installed simultaneously; all loaded adapters receive every
template event and lifecycle hook concurrently.

## Entry point

Adapters register under the `opm.gui_adapter` entry point group:

```toml
# pyproject.toml
[project.entry-points."opm.gui_adapter"]
my-adapter = "my_package:MyGUIPlugin"
```

```python
# setup.py
entry_points={
    "opm.gui_adapter": [
        "my-adapter = my_package:MyGUIPlugin",
    ]
}
```

## Base class — `AbstractGUIPlugin`

**Location:** `ovos_plugin_manager.templates.gui.AbstractGUIPlugin`

```python
from ovos_plugin_manager.templates.gui import AbstractGUIPlugin

class MyGUIPlugin(AbstractGUIPlugin):
    def __init__(self, config, bus=None):
        super().__init__(config, bus)
        # start any servers, load resources, etc.
```

### Constructor

```python
AbstractGUIPlugin(config: dict, bus: MessageBusClient | None = None)
```

| Arg | Description |
|---|---|
| `config` | Plugin-specific configuration dict (from `mycroft.conf` → `gui.adapters.<plugin-name>`) |
| `bus` | The OVOS `MessageBusClient` shared by `ovos-gui`. Available as `self.bus`. |

---

## Template handlers

Override any of these methods to render the corresponding template.
All default to **no-ops**, so you only implement what your adapter supports.

```python
def handle_show_idle(self, skill_id: str, data: dict) -> None: ...
def handle_show_loading(self, skill_id: str, data: dict) -> None: ...
def handle_show_status(self, skill_id: str, data: dict) -> None: ...
def handle_show_error(self, skill_id: str, data: dict) -> None: ...
def handle_show_text(self, skill_id: str, data: dict) -> None: ...
def handle_show_image(self, skill_id: str, data: dict) -> None: ...
def handle_show_animated_image(self, skill_id: str, data: dict) -> None: ...
def handle_show_list(self, skill_id: str, data: dict) -> None: ...
def handle_show_grid(self, skill_id: str, data: dict) -> None: ...
def handle_show_table(self, skill_id: str, data: dict) -> None: ...
def handle_show_html(self, skill_id: str, data: dict) -> None: ...
def handle_show_url(self, skill_id: str, data: dict) -> None: ...
def handle_show_audio_player(self, skill_id: str, data: dict) -> None: ...
def handle_show_video_player(self, skill_id: str, data: dict) -> None: ...
def handle_show_clock(self, skill_id: str, data: dict) -> None: ...
def handle_show_timer(self, skill_id: str, data: dict) -> None: ...
def handle_show_weather(self, skill_id: str, data: dict) -> None: ...
def handle_show_map(self, skill_id: str, data: dict) -> None: ...
def handle_show_confirm(self, skill_id: str, data: dict) -> None: ...
def handle_show_select(self, skill_id: str, data: dict) -> None: ...
def handle_show_face(self, skill_id: str, data: dict) -> None: ...
```

`skill_id` is the namespace (the skill's unique ID).
`data` is the full session data dict for the namespace at the time of the call.
See [templates.md](templates.md) for the exact keys each template places in `data`.

---

## Lifecycle hooks

```python
def on_namespace_activated(self, skill_id: str) -> None: ...
```
Called when a skill's namespace moves to the top of the active stack
(i.e. becomes the currently displayed skill).

```python
def on_namespace_deactivated(self, skill_id: str) -> None: ...
```
Called when a skill clears its namespace (`gui.clear()` / `gui.release()`)
or when the namespace is removed by the idle timer.

```python
def on_idle(self) -> None: ...
```
Called when the GUI returns to the idle/resting state with no active skill.

---

## Session data hook

```python
def on_session_update(self, skill_id: str, data: dict) -> None: ...
```
Called on every `gui.value.set` message — i.e. whenever a skill sets a GUI
variable.  `data` contains all the keys set in that message (reserved keys
`__from`, `__idle`, `__animations` are stripped before delivery).

Adapters that maintain live data bindings (e.g. a browser with SSE push) can
use this hook to push incremental updates without waiting for a template call.

---

## Status event hook

```python
def on_status_event(self, event_name: str, data: dict) -> None: ...
```
Called for well-known OVOS system events forwarded by `NamespaceManager`:

| `event_name` | Meaning |
|---|---|
| `recognizer_loop:wakeword` | Wake word detected |
| `recognizer_loop:record_begin` | Microphone opened |
| `recognizer_loop:record_end` | Microphone closed |
| `recognizer_loop:utterance` | Utterance recognised |
| `recognizer_loop:recognition_unknown` | STT gave no result |
| `speak` | TTS is about to speak |
| `recognizer_loop:audio_output_start` | Audio playback started |
| `recognizer_loop:audio_output_end` | Audio playback ended |
| `recognizer_loop:sleep` | Device going to sleep |
| `recognizer_loop:wake_up` | Device waking up |
| `mycroft.awoken` | Wake-up acknowledged |
| `ovos.utterance.handled` | Intent matched and handled |
| `ovos.utterance.cancelled` | Utterance cancelled |

---

## Template dispatch helper

`AbstractGUIPlugin` includes a convenience dispatcher used internally by
`NamespaceManager`:

```python
adapter.dispatch_template("SYSTEM_weather", skill_id, data)
# → calls adapter.handle_show_weather(skill_id, data)
```

The mapping is defined in `AbstractGUIPlugin._TEMPLATE_HANDLERS` and covers
all 21 `SYSTEM_*` identifiers.

---

## Configuration

Adapter-specific configuration lives under `gui.adapters.<entry-point-name>`
in `mycroft.conf`:

```json
{
  "gui": {
    "adapters": {
      "ovos-legacy-mycroft-gui": {
        "default_qt_version": 5
      },
      "my-adapter": {
        "port": 9090
      }
    }
  }
}
```

The matching dict is passed as `config` to `AbstractGUIPlugin.__init__`.

---

## Factory — `OVOSGUIAdapterFactory`

**Location:** `ovos_plugin_manager.gui_adapter`

### Load all installed adapters (used by `ovos-gui` at startup)

```python
from ovos_plugin_manager.gui_adapter import OVOSGUIAdapterFactory

adapters = OVOSGUIAdapterFactory.create_all(
    config={"my-adapter": {"port": 9090}},
    bus=my_bus,
)
# → List[AbstractGUIPlugin]
```

### Load a single adapter by name

```python
from ovos_plugin_manager.gui_adapter import OVOSGUIAdapterFactory

adapter = OVOSGUIAdapterFactory.create("my-adapter", config={}, bus=my_bus)
```

### Discover installed adapters (without instantiating)

```python
from ovos_plugin_manager.gui_adapter import find_gui_adapter_plugins

plugins = find_gui_adapter_plugins()
# → {"my-adapter": <class MyGUIPlugin>, ...}
```

---

## Minimal adapter example

```python
# my_adapter/__init__.py
from ovos_plugin_manager.templates.gui import AbstractGUIPlugin

class MyGUIPlugin(AbstractGUIPlugin):

    def handle_show_text(self, skill_id, data):
        title = data.get("title", "")
        text = data.get("text", "")
        print(f"[{skill_id}] {title}\n{text}")

    def handle_show_weather(self, skill_id, data):
        print(
            f"[{skill_id}] {data['current_temp']}° "
            f"{data['condition']} @ {data.get('location', '')}"
        )

    def on_namespace_deactivated(self, skill_id):
        print(f"[{skill_id}] screen cleared")
```

```toml
# pyproject.toml
[project.entry-points."opm.gui_adapter"]
my-adapter = "my_adapter:MyGUIPlugin"
```

Install, restart `ovos-gui`, and the adapter will be discovered and loaded
automatically alongside any other installed adapters.
