# Page Templates

Skills display content exclusively through pre-defined page templates.
Custom per-skill QML or HTML is no longer supported through this interface.

All templates are values of the `PageTemplates` enum in `ovos-gui-api-client`:

```python
from ovos_gui_api_client import PageTemplates, GUIInterface, FillMode, ListItem, GridItem, SelectItem
```

---

## Template reference

Each entry lists:
- The **`PageTemplates` enum value** (also the SYSTEM_* identifier sent on the bus)
- The **`GUIInterface` method** skills call
- The **session data keys** the display adapter receives in `data`

---

### IDLE — `SYSTEM_idle`

Reserved for the `ovos-gui` service. Skills must not call this directly.
Adapters use it to render the resting / home screen.

---

### LOADING — `SYSTEM_loading`

```python
gui.show_loading(text="")
```

| Key | Type | Description |
|---|---|---|
| `label` | `str` | Text shown below the spinner |

---

### STATUS — `SYSTEM_status`

```python
gui.show_status(text, success)
```

| Key | Type | Description |
|---|---|---|
| `label` | `str` | Message to display |
| `success` | `bool` | `True` = success (green), `False` = failure (red) |

---

### ERROR — `SYSTEM_error`

```python
gui.show_error(text, detail=None)
```

| Key | Type | Description |
|---|---|---|
| `label` | `str` | Primary error message |
| `detail` | `str \| None` | Optional secondary text / traceback |

---

### TEXT — `SYSTEM_text`

```python
gui.show_text(text, title=None)
```

| Key | Type | Description |
|---|---|---|
| `text` | `str` | Body text (may be long; adapters should paginate or scroll) |
| `title` | `str \| None` | Optional heading |

---

### IMAGE — `SYSTEM_image`

```python
gui.show_image(url, caption=None, title=None, fill=None, background_color=None)
```

| Key | Type | Description |
|---|---|---|
| `image` | `str` | HTTP(S) URL or absolute local file path |
| `title` | `str \| None` | Heading above the image |
| `caption` | `str \| None` | Caption below the image |
| `fill` | `str \| None` | `"fit"` \| `"crop"` \| `"stretch"` (see `FillMode`) |
| `background_color` | `str \| None` | Hex background colour, e.g. `"#000000"` |

---

### ANIMATED_IMAGE — `SYSTEM_animated_image`

```python
gui.show_animated_image(url, caption=None, title=None, fill=None, background_color=None)
# or
gui.show_image(url, ..., animated=True)
```

Same session data keys as IMAGE.

---

### LIST — `SYSTEM_list`

```python
gui.show_list(items, title=None)
# items: List[ListItem | dict]
```

| Key | Type | Description |
|---|---|---|
| `title` | `str \| None` | Optional heading |
| `items` | `list[dict]` | Each item: `{"title": str, "subtitle": str?, "image": str?}` |

`ListItem` dataclass:
```python
@dataclass
class ListItem:
    title: str
    subtitle: Optional[str] = None
    image: Optional[str] = None   # URL or path
```

---

### GRID — `SYSTEM_grid`

```python
gui.show_grid(items, title=None)
# items: List[GridItem | dict]
```

| Key | Type | Description |
|---|---|---|
| `title` | `str \| None` | Optional heading |
| `items` | `list[dict]` | Each item: `{"image": str, "title": str?}` |

`GridItem` dataclass:
```python
@dataclass
class GridItem:
    image: str            # URL or path (required)
    title: Optional[str] = None
```

---

### TABLE — `SYSTEM_table`

```python
gui.show_table(columns, rows, title=None)
```

| Key | Type | Description |
|---|---|---|
| `title` | `str \| None` | Optional heading |
| `columns` | `list[str]` | Column header names |
| `rows` | `list[list]` | Each row: ordered values aligned to `columns` |

Row length must equal column count; `show_table` raises `ValueError` otherwise.

---

### HTML — `SYSTEM_html`

```python
gui.show_html(html, resource_url=None)
```

| Key | Type | Description |
|---|---|---|
| `html` | `str` | Raw HTML string to render |
| `resource_url` | `str \| None` | Base URL for resolving relative resources |

---

### URL — `SYSTEM_url`

```python
gui.show_url(url)
```

| Key | Type | Description |
|---|---|---|
| `url` | `str` | Fully-qualified URL to load in the web renderer |

---

### AUDIO_PLAYER — `SYSTEM_audio_player`

```python
gui.show_audio_player(title, artist=None, album=None, image=None,
                       position=0.0, duration=0.0, playing=True)
```

| Key | Type | Description |
|---|---|---|
| `title` | `str` | Track title |
| `artist` | `str \| None` | Artist name |
| `album` | `str \| None` | Album name |
| `image` | `str \| None` | URL or path to album art |
| `position` | `float` | Current playback position in seconds |
| `duration` | `float` | Total duration in seconds (`0` = unknown / streaming) |
| `playing` | `bool` | `True` = playing, `False` = paused |

Call again on track change or play/pause to keep the display in sync.

---

### VIDEO_PLAYER — `SYSTEM_video_player`

```python
gui.show_video_player(uri, title=None, playing=True)
```

| Key | Type | Description |
|---|---|---|
| `uri` | `str` | URI of the video stream or file |
| `title` | `str \| None` | Optional title overlay |
| `playing` | `bool` | `True` = start immediately, `False` = paused |

---

### CLOCK — `SYSTEM_clock`

```python
gui.show_clock()
```

No session data required. The display layer is self-updating.

---

### TIMER — `SYSTEM_timer`

```python
gui.show_timer(end_time, label=None, count_up=False)
```

| Key | Type | Description |
|---|---|---|
| `end_time` | `float` | Unix timestamp when the timer expires (use `time.time() + seconds`) |
| `label` | `str \| None` | Optional label, e.g. `"Pasta"` |
| `count_up` | `bool` | `False` = countdown; `True` = stopwatch (count up from `end_time`) |

The display layer derives the displayed time from `end_time` and the device
clock — no polling from the skill is needed.

---

### WEATHER — `SYSTEM_weather`

```python
gui.show_weather(current_temp, min_temp, max_temp, condition,
                  icon=None, location=None)
```

| Key | Type | Description |
|---|---|---|
| `current_temp` | `int \| float` | Current temperature |
| `min_temp` | `int \| float` | Daily low |
| `max_temp` | `int \| float` | Daily high |
| `condition` | `str` | Human-readable condition label |
| `icon` | `str \| None` | URL or path to a weather icon |
| `location` | `str \| None` | Location name to display |

---

### MAP — `SYSTEM_map`

```python
gui.show_map(latitude, longitude, zoom=12, label=None)
```

| Key | Type | Description |
|---|---|---|
| `latitude` | `float` | WGS-84 latitude in decimal degrees |
| `longitude` | `float` | WGS-84 longitude in decimal degrees |
| `zoom` | `int` | Zoom level (1 = world, 20 = building); default 12 |
| `label` | `str \| None` | Optional place annotation |

---

### CONFIRM — `SYSTEM_confirm`

```python
gui.show_confirm(question)
```

| Key | Type | Description |
|---|---|---|
| `question` | `str` | The question being asked |

OVOS is voice-first. This template is a **visual accompaniment only** — the
skill must also ask the question via `self.ask_yesno()` or speech. A touch
shortcut (if the adapter supports it) fires:

```
<skill_id>.confirm.response  →  {"confirmed": bool}
```

The skill must register a handler for that event *and* handle the spoken reply.

---

### SELECT — `SYSTEM_select`

```python
gui.show_select(items, prompt=None)
# items: List[SelectItem | dict]
```

| Key | Type | Description |
|---|---|---|
| `prompt` | `str \| None` | Optional spoken prompt echoed on screen |
| `items` | `list[dict]` | Each item: `{"label": str, "value": any}` |

`SelectItem` dataclass:
```python
@dataclass
class SelectItem:
    label: str   # text shown to the user
    value: Any   # machine value returned on selection
```

A touch shortcut fires:

```
<skill_id>.select.response  →  {"value": <selected value>}
```

---

### FACE — `SYSTEM_face`

```python
gui.show_face(awake=True)
```

| Key | Type | Description |
|---|---|---|
| `sleeping` | `bool` | `False` = awake (open eyes); `True` = sleeping |

Intended for avatar-style frontends. Called automatically by the listener
service on wake-word detection and sleep.

---

## FillMode

Used by `show_image()` to control image scaling:

```python
class FillMode(str, enum.Enum):
    FIT     = "fit"      # preserve aspect ratio, letterbox
    CROP    = "crop"     # fill area, crop overflow
    STRETCH = "stretch"  # fill area exactly, ignore aspect ratio
```

---

## Session data access in adapters

When `handle_show_weather(skill_id, data)` is called, `data` is the full
namespace session dict at the time of the call:

```python
def handle_show_weather(self, skill_id, data):
    temp = data.get("current_temp")
    condition = data.get("condition")
    icon = data.get("icon")
    # render…
```

Keys in `data` match exactly the table entries above.
