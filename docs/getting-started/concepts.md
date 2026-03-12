# Core Concepts — OVOS GUI

Essential terminology and mental models for understanding the OVOS GUI system.

## Overview

The OVOS GUI layer enables skills to display information on any device — desktop, tablet, web browser, or embedded screen — **without knowing anything about the display technology**.

**Key insight**: Skills define *what* to show (a weather template), not *how* to show it. Adapters handle the rendering.

---

## 1. Templates

A **template** is a standardized data structure for a type of content.

### Example: Weather Template

```python
# In a skill
self.gui.show_weather(
    current_temp=22,
    min_temp=18,
    max_temp=26,
    condition="Partly Cloudy",
    location="Berlin",
    icon="cloud.png"
)
```

The skill says "show weather with these values" but doesn't care if it appears in:
- A QML desktop app (Qt5)
- A web page (HTML)
- A smart display (WebSocket)
- A terminal (TUI)

Every adapter that knows about the **weather template** can render it.

### OVOS Provides 21 Templates

Common templates include:
- **weather** — Current conditions, forecast
- **music** — Song info, album art, playback controls
- **news** — Articles with headlines
- **weather.forecast** — Extended forecast
- **reminder** — Notification display
- **generic** — Custom data (flexible)
- And 14 more...

See [Templates.md](templates.md) for the complete list and all required/optional fields.

---

## 2. Namespaces

A **namespace** is a logical "window" or "app space" for a skill or system component.

### Namespace Naming

Namespaces follow the OVOS skill ID format:

```
<creator>-<name>.<domain>
```

Examples:
- `skill-weather.openvoiceos` — The OVOS weather skill
- `skill-news.openvoiceos` — A news skill
- `skill-music.openvoiceos` — A music player
- `system` — System-level GUI (home screen, settings)

### What a Namespace Contains

Each namespace has:
- **Pages**: One or more screens (e.g., "current weather", "forecast")
- **Session data**: Temporary state shared with the adapter (e.g., user selections)
- **Active page**: Which page is currently displayed
- **Ownership**: Which skill or system component owns it

### Example: Music Skill Namespace

The music skill might have:
1. **nowplaying** page — Shows current song, album art, playback controls
2. **playlist** page — Shows the queue
3. **search** page — Search results

The adapter receives messages like:

```
gui.page_show {
  namespace: "skill-music.openvoiceos",
  page: "nowplaying",
  data: {
    title: "Bohemian Rhapsody",
    artist: "Queen",
    album_art: "https://...",
    duration: 354,
    elapsed: 120
  }
}
```

---

## 3. Pages

A **page** is a single screen or view within a namespace.

### Page Properties

- **Name**: Identifier within the namespace (e.g., "current", "forecast")
- **Template**: The data schema it uses (e.g., "weather", "music")
- **Data**: The actual content (values for the template)
- **Persistent**: Whether it survives a skill restart (default: false)
- **Duration**: How long to display before returning to idle (optional)

### Page Lifecycle

```
Skill → show_weather()
     ↓
GUI Service → Create/update namespace "skill-weather"
           ↓
           → Create page "current" with template "weather"
           ↓
Adapter → Receives gui.page_show message
       ↓
       → Renders the page
       ↓
User → Interacts with display
    ↓
    → Sends gui.user_input message back
    ↓
Skill → Receives message, handles interaction
```

### Persistent Pages

Some pages should survive skill restarts:

```python
self.gui.show_page(
    "mypage.qml",
    {
        "title": "Persistent Data",
        "value": 42
    },
    persistent=True,
    duration=3600  # 1 hour
)
```

The page remains displayed even if the skill crashes and restarts.

---

## 4. Session Data

**Session data** is temporary state shared between a skill and its adapter(s).

### Use Cases

1. **User selections**: Which item in a list the user tapped
2. **Scroll position**: Where the user scrolled to
3. **Form input**: Text the user typed
4. **Playback position**: Current song position

### Setting Session Data

```python
# In the skill
self.gui.set_context({
    "current_selection": 5,
    "user_name": "Alice",
    "volume_level": 75
})
```

### Receiving Session Data

The adapter sends updates when the user interacts:

```python
def on_gui_session_update(self, message):
    """Skill receives session updates from adapter."""
    data = message.data
    current_selection = data.get("current_selection")
    # Handle user interaction
```

### Reserved Keys

The following keys are reserved by the system and cannot be used:

- `__idle` — Idle display timeout
- `__duration` — Page display duration
- `__persistent` — Persistence flag
- Any key starting with `__`

---

## 5. The MessageBus

All GUI communication flows through the **OVOS MessageBus** — a WebSocket-based pub/sub system.

### MessageBus Basics

Every message has:
- **type**: Event identifier (e.g., `gui.page_show`)
- **data**: JSON payload
- **context**: Metadata (origin, timestamp)

### Key GUI Messages

**Skills → GUI Service**

```python
{
  "type": "gui.request_page",
  "data": {
    "page": "weather.qml",
    "resources": [...],
    "namespace": "skill-weather.openvoiceos",
    "skill_id": "skill-weather.openvoiceos"
  }
}
```

**GUI Service → Adapters**

```python
{
  "type": "gui.page_show",
  "data": {
    "namespace": "skill-weather.openvoiceos",
    "page": "weather",
    "data": {
      "current_temp": 22,
      "condition": "Cloudy",
      ...
    }
  }
}
```

**Adapter → GUI Service**

```python
{
  "type": "gui.user_input",
  "data": {
    "namespace": "skill-weather.openvoiceos",
    "page": "weather",
    "action": "next_day"
  }
}
```

See [Bus Protocol Reference](bus-protocol.md) for the complete list.

---

## 6. Adapters

An **adapter** is a GUI plugin that:
1. Listens to GUI events on the MessageBus
2. Receives template data as JSON
3. Renders it in its own framework
4. Sends user interactions back via MessageBus

### Built-in Adapters

| Adapter | Framework | Use Case |
|---------|-----------|----------|
| `ovos-legacy-mycroft-gui-plugin` | Qt5/QML | Desktop displays |
| `ovos-gui-plugin-web` | HTML/CSS/JS | Web browsers, tablets |
| `ovos-gui-debug-tui` | Terminal | Headless debugging |

### Custom Adapters

You can build adapters for any platform:
- **Mobile**: Build an Android adapter
- **Smart displays**: Amazon Echo Show, Google Nest
- **Embedded**: Raspberry Pi with custom UI
- **Terminal**: TUI (text UI) adapter
- **IoT**: Any WebSocket-capable device

See [Adapter Plugin System](adapter-plugins.md) for how to build one.

### Adapter Lifecycle

```
Adapter starts
    ↓
Connects to MessageBus
    ↓
Announces itself: "gui_show_page" capability
    ↓
Listens for gui.page_show messages
    ↓
When message arrives:
  - Parse JSON data
  - Determine template type
  - Render using native widgets
    ↓
User interacts with display
    ↓
Send gui.user_input message
    ↓
(Loop)
```

---

## 7. GUIInterface (The Skill API)

**GUIInterface** is the API that skills use to show GUI content. It provides 21 template methods:

```python
from ovos_workshop.skills import OVOSSkill

class MySkill(OVOSSkill):
    def handle_intent(self, message):
        # The GUIInterface is auto-injected as self.gui
        self.gui.show_weather(...)
        self.gui.show_music(...)
        self.gui.show_news(...)
        # etc.
```

Under the hood, `self.gui.show_weather(...)` translates to:

```python
def show_weather(self, **kwargs):
    self.gui.show_page(
        "weather.qml",  # Template name
        kwargs,         # Data
        override_idle=True,
        override_pg=False
    )
```

Which sends a message to the GUI service:

```python
{
  "type": "gui.request_page",
  "data": {
    "page": "weather.qml",
    "namespace": self.skill_id,
    "data": kwargs
  }
}
```

See [Skill GUI Development](skill-gui-development.md) for all 21 template methods.

---

## 8. Skill IDs

A **skill ID** is a unique identifier for a skill:

```
<creator>-<name>.<domain>
```

Examples:
- `openvoiceos-weather.openvoiceos` — Official OVOS weather skill
- `john-music-player.mycroft` — John's custom music player
- `company-internal-tool.local` — Internal company tool

The skill ID is used for:
- **Namespace naming**: `skill-weather.openvoiceos`
- **Routing GUI events**: Which skill gets user input?
- **Session isolation**: Each skill's data is separate

---

## 9. Context & Threading

The OVOS GUI system is **event-driven** and **non-blocking**:

- Showing a page is **async** — your skill doesn't wait
- User input is **async** — handled via `on_gui_event` handlers
- Session updates are **async** — streamed as events

This means:

```python
def handle_intent(self, message):
    self.gui.show_weather(...)
    # ↓ The skill continues immediately, doesn't wait for render
    self.speak("Here's the weather")
    # ↓ Meanwhile, the adapter is rendering the page
```

To handle user input, define event handlers:

```python
def on_gui_give_feedback(self, message):
    """Fired when user gives feedback via GUI."""
    feedback = message.data.get("feedback")
    self.log.info(f"User gave: {feedback}")
```

---

## 10. Performance Considerations

### For Skills

- **Minimize payload**: Send only needed data (< 10 KB per page)
- **Batch updates**: Use `show_page()` once instead of many small updates
- **Cache resources**: Don't re-fetch images/data for every page

### For Adapters

- **Render quickly**: Page changes should appear in < 500ms
- **Update efficiently**: Only re-render changed elements
- **Handle offline**: Gracefully degrade if MessageBus is slow

See [Performance Optimization](performance.md) for details.

---

## 11. Reserved Keywords

Do not use these keys in your page data:

| Key | Purpose |
|-----|---------|
| `__idle` | Idle display timeout |
| `__persistent` | Page persistence flag |
| `__duration` | Display duration override |
| `__location` | (Reserved for future use) |

---

## Summary

| Concept | Definition | Example |
|---------|-----------|---------|
| **Template** | Standardized data schema | Weather, Music, News |
| **Namespace** | Logical window for a skill | `skill-weather.openvoiceos` |
| **Page** | Single screen within namespace | `current`, `forecast` |
| **Session** | Temporary shared state | User selections, scroll position |
| **MessageBus** | Event broker for all communication | WebSocket pub/sub |
| **Adapter** | GUI renderer plugin | Qt5, Web, TUI |
| **GUIInterface** | Skill API for showing content | `self.gui.show_weather()` |
| **Skill ID** | Unique skill identifier | `openvoiceos-weather.openvoiceos` |

---

## Next Steps

- **Use these concepts**: [Skill GUI Development](skill-gui-development.md)
- **See them in action**: [Skill Examples](skill-examples.md)
- **Reference all templates**: [Templates.md](templates.md)
- **Build adapters**: [Adapter Plugin System](adapter-plugins.md)
