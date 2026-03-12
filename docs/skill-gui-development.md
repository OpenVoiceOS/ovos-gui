# Skill GUI Development — Using Templates in Your Skill

Complete guide to adding GUI features to your OVOS skill using the template API.

## Overview

The OVOS GUI system provides **21 standardized templates** that you can use to display content. You don't write QML, HTML, or CSS — just call a template method with your data.

```python
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder

class WeatherSkill(OVOSSkill):
    @intent_handler(IntentBuilder("WeatherIntent").require("weather"))
    def handle_weather(self, message):
        # Call a template method
        self.gui.show_weather(
            current_temp=22,
            condition="Cloudy",
            location="Berlin"
        )
```

That's it. Any installed display adapter (Qt5, web, etc.) will render it.

---

## Getting Started

### 1. Import GUIInterface

The `OVOSSkill` base class automatically provides `self.gui`:

```python
from ovos_workshop.skills import OVOSSkill

class MySkill(OVOSSkill):
    def handle_intent(self, message):
        self.gui.show_weather(...)  # Use it here
```

No explicit import needed.

### 2. Choose a Template

Browse [Templates.md](templates.md) for all 21 options. Common ones:

- `show_weather()` — Weather conditions and forecasts
- `show_music()` — Now playing, queue, controls
- `show_news()` — News articles and headlines
- `show_image()` — Display images
- `show_text()` — Display text content
- `show_generic()` — Custom structured data
- And 15 more...

### 3. Call the Template

```python
self.gui.show_weather(
    current_temp=22,
    condition="Cloudy",
    location="Berlin",
    icon="cloud.png"
)
```

The skill continues immediately — the GUI rendering happens asynchronously.

---

## Template Methods (21 Available)

### Core Templates

#### 1. show_weather()
Display current weather and forecasts.

```python
self.gui.show_weather(
    current_temp=22,
    min_temp=18,
    max_temp=26,
    condition="Partly Cloudy",
    location="Berlin",
    icon="cloud.png",
    humidity=65,
    wind_speed=15,
    wind_direction="NW"
)
```

#### 2. show_music()
Display music/audio playback.

```python
self.gui.show_music(
    title="Bohemian Rhapsody",
    artist="Queen",
    album="A Night at the Opera",
    album_art="https://example.com/album.jpg",
    duration=354,
    elapsed=120,
    playlist_size=50,
    playlist_index=5,
    support_next=True,
    support_previous=True,
    can_stream=True
)
```

#### 3. show_news()
Display news articles.

```python
self.gui.show_news(
    articles=[
        {
            "title": "Breaking News",
            "summary": "Important story...",
            "image": "https://example.com/img.jpg",
            "source": "BBC News"
        },
        # ... more articles
    ]
)
```

#### 4. show_image()
Display a single image.

```python
self.gui.show_image(
    image="https://example.com/photo.jpg",
    caption="Beautiful Sunset",
    title="Photo Gallery"
)
```

#### 5. show_text()
Display text content (paragraphs, lists, etc.).

```python
self.gui.show_text(
    title="My Page",
    text="This is paragraph text...",
    bullets=[
        "Item 1",
        "Item 2",
        "Item 3"
    ]
)
```

#### 6. show_generic()
Display custom, unstructured data.

```python
self.gui.show_generic(
    data={
        "anything": "goes here",
        "nested": {
            "custom": "structure"
        },
        "lists": [1, 2, 3]
    }
)
```

### Additional Templates

| Template | Purpose |
|----------|---------|
| `show_question()` | Ask user a yes/no question |
| `show_list()` | Scrollable list with selection |
| `show_grid()` | Grid of items with images |
| `show_timer()` | Timer/countdown display |
| `show_reminder()` | Reminder notification |
| `show_notification()` | General notification |
| `show_dial()` | Dial/gauge display |
| `show_settings()` | Settings form |
| `show_confirmation()` | Confirmation dialog |
| `show_loading()` | Loading spinner |
| `show_error()` | Error message |
| `show_success()` | Success confirmation |
| `show_idle()` | Idle/home screen |
| `show_page()` | Custom page (advanced) |

See [Templates.md](templates.md) for complete parameter lists.

---

## Handling User Input

When a user interacts with the GUI (taps a button, swipes, etc.), the adapter sends an event back:

### Listen for Events

Define event handlers in your skill:

```python
def initialize(self):
    """Called when skill is loaded."""
    self.gui.register_handler(
        "mypage.button_clicked",
        self.on_button_clicked
    )
    self.gui.register_handler(
        "mypage.selection_changed",
        self.on_selection_changed
    )

def on_button_clicked(self, message):
    """Fired when user clicks a button."""
    button_id = message.data.get("button_id")
    self.log.info(f"User clicked button: {button_id}")
    # Respond to user
    self.speak(f"You clicked {button_id}")

def on_selection_changed(self, message):
    """Fired when user selects an item."""
    selected_index = message.data.get("selected")
    self.log.info(f"User selected: {selected_index}")
```

### Common Events

```python
# List selection
self.gui.register_handler("mypage.item_selected", self.on_item_selected)

# Button press
self.gui.register_handler("mypage.button_pressed", self.on_button_pressed)

# Slider/dial change
self.gui.register_handler("mypage.value_changed", self.on_value_changed)

# Text input
self.gui.register_handler("mypage.text_input", self.on_text_input)

# Generic action
self.gui.register_handler("mypage.action", self.on_action)
```

---

## Displaying Multiple Pages

### Sequential Pages

Show pages one after another:

```python
def handle_weather_intent(self, message):
    # Show current weather
    self.gui.show_weather(
        current_temp=22,
        condition="Cloudy",
        location="Berlin"
    )

    # After 5 seconds, show forecast
    time.sleep(5)
    self.gui.show_weather_forecast(
        forecast=[
            {"day": "Monday", "high": 24, "low": 18},
            {"day": "Tuesday", "high": 22, "low": 16},
            {"day": "Wednesday", "high": 20, "low": 14},
        ]
    )
```

### Using `show_page()` for Advanced Control

```python
# Show page with options
self.gui.show_page(
    "mypage.qml",
    {
        "title": "My Page",
        "content": "..."
    },
    override_idle=True,        # Show even if skill wasn't the last active
    override_pg=False,         # Don't override already-showing page
    persistent=False,          # Don't keep if skill restarts
    duration=10                # Auto-dismiss after 10 seconds
)
```

---

## Session Data

**Session data** is temporary state shared between your skill and the adapter.

### Setting Session Data

```python
def handle_intent(self, message):
    self.gui.show_list(items=["Option A", "Option B", "Option C"])

    # Store state in session
    self.gui.set_context({
        "current_selection": 0,
        "total_items": 3
    })
```

### Receiving Session Updates

```python
def initialize(self):
    self.gui.register_handler(
        "mypage.session_update",
        self.on_session_update
    )

def on_session_update(self, message):
    """Called when adapter updates session data."""
    selection = message.data.get("current_selection")
    self.log.info(f"User selected index: {selection}")
```

### Clearing Session

```python
def shutdown(self):
    """Called when skill is stopped."""
    self.gui.clear_context()
```

---

## Best Practices

### 1. Keep Payloads Small

Minimize data sent to adapters:

```python
# ❌ Bad: Sending entire database
self.gui.show_list(
    items=database.get_all_users()  # Potentially 1000s of items
)

# ✅ Good: Send only what's visible
self.gui.show_list(
    items=database.get_users(limit=20)  # Just the first page
)
```

### 2. Provide Fallback Text

Always have a voice alternative:

```python
# Show GUI content
self.gui.show_weather(
    current_temp=22,
    condition="Cloudy"
)

# Also speak (for users without a display)
self.speak_dialog("weather", data={
    "temp": 22,
    "condition": "Cloudy"
})
```

### 3. Handle Missing Adapter

Not all users have a display adapter:

```python
def handle_intent(self, message):
    if self.gui.connected:  # Check if adapter is connected
        self.gui.show_weather(...)

    # Always have a voice fallback
    self.speak_dialog("weather_dialog")
```

### 4. Clean Up Event Handlers

Remove handlers when no longer needed:

```python
def shutdown(self):
    """Called when skill stops."""
    self.gui.remove_handler("mypage.button_clicked")
    self.gui.remove_handler("mypage.item_selected")
    self.gui.clear_context()
```

### 5. Use Meaningful Event Names

```python
# ❌ Confusing
self.gui.register_handler("page.event", self.handler)

# ✅ Clear
self.gui.register_handler("weather.next_day_clicked", self.on_next_day)
self.gui.register_handler("news.article_selected", self.on_article_selected)
```

### 6. Document Your GUI Contract

```python
class WeatherSkill(OVOSSkill):
    """Weather skill with GUI.

    GUI Events:
        weather.next_day_clicked: User wants to see next day
        weather.location_changed: User changed location

    Templates Used:
        show_weather: Current conditions
        show_weather_forecast: Extended forecast
    """
```

---

## Troubleshooting

### GUI Doesn't Appear

1. **Check adapter is running**:
   ```bash
   ps aux | grep gui
   ```

2. **Check skill is active**:
   ```bash
   # In OVOS logs, look for skill activation
   tail -f ~/.local/share/ovos/logs/skills.log
   ```

3. **Check MessageBus connection**:
   ```python
   if self.gui.connected:
       print("Adapter is connected")
   else:
       print("No adapter connected")
   ```

4. **Enable debug logging**:
   ```python
   from ovos_utils.log import LOG
   LOG.setLevel("DEBUG")
   self.gui.show_weather(...)
   ```

### Event Handler Not Firing

1. **Check handler is registered**:
   ```python
   def initialize(self):
       self.gui.register_handler(
           "mypage.button_clicked",
           self.on_button_clicked
       )
       # Handler is now active
   ```

2. **Check event name matches adapter**:
   - Adapter must emit event with exact name
   - Check adapter documentation or logs

3. **Use wildcard listener for debugging**:
   ```python
   self.gui.register_handler(
       "mypage.*",  # Catch all mypage.* events
       self.on_any_event
   )
   ```

### Data Not Updating

1. **Call show_page() again** to refresh:
   ```python
   self.gui.show_weather(
       current_temp=23,  # Updated value
       ...
   )
   ```

2. **Use session updates** for small changes:
   ```python
   self.gui.set_context({
       "current_temp": 23  # Only update this field
   })
   ```

---

## See Also

- **[Templates.md](templates.md)** — All 21 templates with full parameters
- **[Skill Examples](skill-examples.md)** — Copy-paste examples
- **[Core Concepts](concepts.md)** — Understanding namespaces and pages
- **[Advanced: Session State](advanced-state.md)** — Managing persistent data
- **[Testing GUI](testing-gui.md)** — Unit testing GUI features
