# Skill Migration Guide

This guide shows how to migrate an existing OVOS/Mycroft skill from the old
`show_page()` API to the new template-based `GUIInterface`.

---

## What changes

| Before | After |
|---|---|
| Skills ship `gui/qt5/*.qml`, `gui/qt6/*.qml`, `gui/py-htmx/*.py` | No framework assets in skills at all |
| `self.gui.show_page("MyPage")` | `self.gui.show_weather(...)`, `self.gui.show_text(...)`, etc. |
| `self.gui["key"] = value` then `show_page()` | One typed call sets data and triggers display |
| QML reads skill-provided session data | Bundled QML in `ovos-legacy-mycroft-gui-plugin` reads standardised keys |
| Skill breaks on devices without matching QML renderer | Skill works on all renderers (Qt, browser, TUI, …) automatically |

---

## Step-by-step

### 1. Remove framework asset directories

Delete everything under:

```
gui/
  qt5/
  qt6/
  py-htmx/
```

If the skill repo has no other reason to keep these directories, remove them entirely.

---

### 2. Replace `show_page()` calls

Find every `self.gui.show_page()` / `self.gui.show_pages()` call and replace it with
the appropriate typed method. The full list is in [templates.md](templates.md).

---

### 3. Verify dependencies

`self.gui` is now a `GUIInterface` from `ovos-gui-api-client`. It is provided by
`ovos-workshop` — no change needed in skill requirements.

---

## Migration examples

### Weather skill

**Before:**
```python
def handle_weather_intent(self, message):
    weather = self._get_weather()
    self.gui["current_temp"] = weather.temp
    self.gui["condition"]    = weather.condition
    self.gui["icon"]         = weather.icon_path       # local file
    self.gui["location"]     = weather.city
    self.gui.show_page("CurrentWeather")
```

**After:**
```python
def handle_weather_intent(self, message):
    weather = self._get_weather()
    self.gui.show_weather(
        current_temp=weather.temp,
        min_temp=weather.temp_min,
        max_temp=weather.temp_max,
        condition=weather.condition,
        icon=weather.icon_path,     # local path or URL — both accepted
        location=weather.city,
    )
```

---

### Text / reading skill

**Before:**
```python
def show_article(self, title, body):
    self.gui["title"] = title
    self.gui["text"]  = body
    self.gui.show_page("Article")
```

**After:**
```python
def show_article(self, title, body):
    self.gui.show_text(body, title=title)
```

---

### Image display skill

**Before:**
```python
self.gui["image"] = image_url
self.gui["caption"] = caption
self.gui.show_page("ImageView")
```

**After:**
```python
self.gui.show_image(image_url, caption=caption)
```

For animated GIFs:
```python
self.gui.show_animated_image(gif_url, caption=caption)
# or
self.gui.show_image(gif_url, animated=True)
```

---

### Audio player skill

**Before:**
```python
self.gui["title"]    = track.title
self.gui["artist"]   = track.artist
self.gui["image"]    = track.album_art
self.gui["duration"] = track.duration
self.gui["position"] = 0.0
self.gui["playing"]  = True
self.gui.show_page("AudioPlayer")
```

**After:**
```python
self.gui.show_audio_player(
    title=track.title,
    artist=track.artist,
    image=track.album_art,
    duration=track.duration,
    position=0.0,
    playing=True,
)
```

Call again on play/pause or track change to keep the display in sync:
```python
def on_pause(self):
    self.gui.show_audio_player(title=..., playing=False, position=self._position)
```

---

### Video player skill

**Before:**
```python
self.gui["video"] = stream_url
self.gui.show_page("VideoPlayer")
```

**After:**
```python
self.gui.show_video_player(stream_url, title="My Video", playing=True)
```

---

### Clock / date-time skill

**Before:**
```python
self.gui.show_page("time")
# later
self.gui.show_page("date")
```

**After:**
```python
# show a self-updating clock face
self.gui.show_clock()

# show a text date
self.gui.show_text(date_string, title="Today")
```

---

### Timer skill

**Before:**
```python
end_ts = time.time() + seconds
self.gui["end_time"] = end_ts
self.gui["label"]    = label
self.gui.show_page("Timer")
```

**After:**
```python
self.gui.show_timer(
    end_time=time.time() + seconds,
    label=label,
)
```

For a stopwatch (count up):
```python
self.gui.show_timer(end_time=time.time(), count_up=True)
```

---

### List / menu skill

**Before:**
```python
self.gui["items"] = [{"title": x} for x in options]
self.gui.show_page("Menu")
```

**After:**
```python
from ovos_gui_api_client import ListItem

self.gui.show_list(
    items=[ListItem(title=x) for x in options],
    title="Choose one",
)
```

Or pass plain dicts:
```python
self.gui.show_list(
    items=[{"title": x, "subtitle": desc} for x, desc in pairs],
)
```

---

### Confirmation dialog

**Before:**
```python
self.gui["question"] = "Are you sure?"
self.gui.show_page("Confirm")
```

**After:**
```python
self.gui.show_confirm("Are you sure?")
```

Always pair with a spoken confirmation and register the touch response handler:

```python
def initialize(self):
    self.add_event(f"{self.skill_id}.confirm.response", self._on_confirm_touch)

def _on_confirm_touch(self, message):
    confirmed = message.data.get("confirmed")
    # handle touch response
```

---

### Selection dialog

**Before:**
```python
self.gui["items"] = [{"label": x, "value": v} for x, v in choices]
self.gui.show_page("Select")
```

**After:**
```python
from ovos_gui_api_client import SelectItem

self.gui.show_select(
    items=[SelectItem(label=x, value=v) for x, v in choices],
    prompt="Which city?",
)
```

Register the touch response handler:
```python
def initialize(self):
    self.add_event(f"{self.skill_id}.select.response", self._on_select_touch)

def _on_select_touch(self, message):
    value = message.data.get("value")
    # handle selection
```

---

### Status / error feedback

**Before:**
```python
self.gui["label"]   = "Done!"
self.gui["success"] = True
self.gui.show_page("Status")
```

**After:**
```python
self.gui.show_status("Done!", success=True)
# or on failure:
self.gui.show_status("Something went wrong", success=False)
# with detail:
self.gui.show_error("Connection failed", detail=str(exc))
```

---

### Loading indicator

**Before:**
```python
self.gui["label"] = "Searching..."
self.gui.show_page("Loading")
```

**After:**
```python
self.gui.show_loading("Searching...")
```

---

### HTML / web content

**Before:**
```python
self.gui["html"] = rendered_html
self.gui.show_page("Html")
```

**After:**
```python
self.gui.show_html(rendered_html)
# or to load a URL directly:
self.gui.show_url("https://example.com")
```

---

### Map display

**Before:**
```python
self.gui["lat"] = lat
self.gui["lon"] = lon
self.gui.show_page("Map")
```

**After:**
```python
self.gui.show_map(latitude=lat, longitude=lon, zoom=14, label="Here")
```

---

## Releasing the display

To clear the GUI when your skill is done (unchanged):

```python
self.gui.release()
```

This calls `ovos.gui.screen.close` on the bus, which triggers
`on_namespace_deactivated()` on all loaded adapters.

---

## Image paths

Local file paths are accepted anywhere an image URL is expected.
Pass the absolute path as-is:

```python
icon = "/usr/share/icons/my-icon.png"
self.gui.show_image(icon)
self.gui.show_weather(..., icon=icon)
```

---

## What you do NOT need to do

- Do not convert images to base64 yourself — pass paths or URLs directly.
- Do not set `self.gui["key"] = value` before calling a typed method — the method handles data internally.
- Do not call `self.gui.setup_default_handlers()` — it is called automatically.
- Do not ship any QML, Python page classes, or HTML templates inside your skill.
