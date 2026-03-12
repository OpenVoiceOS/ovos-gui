# Advanced: Session State Management

Managing persistent data and state across pages and skill sessions.

## Overview

While [Session Data](concepts.md#session-data) is temporary (lost when page changes), sometimes you need state to persist across:
- Multiple pages within a namespace
- The lifetime of a skill session
- Even skill restarts (for critical data)

This guide covers advanced state management patterns.

---

## Types of State

### 1. Temporary Session State

Survives: While a page is active
Lost: When user navigates or closes the page

```python
def show_list(self):
    """Show list and store selection state."""
    items = ["Option A", "Option B", "Option C"]

    self.gui.show_list(
        title="Choose an option",
        items=items
    )

    # Session state (lives during this page)
    self.gui.set_context({
        "current_selection": 0,  # Which item is selected
        "total_items": len(items)
    })
```

### 2. Skill Instance State

Survives: The entire skill session (while skill is running)
Lost: When skill stops

```python
class MusicSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Instance variables persist while skill is running
        self.current_playlist = []
        self.current_index = 0
        self.is_playing = False
```

### 3. Persistent State

Survives: Skill restarts, even if the service reboots
Stored: In skill settings or database

```python
def save_user_preference(self, preference_name, value):
    """Save state to persistent storage."""
    # Saved to ~/.local/share/ovos/skills/<skill-id>/settings.json
    self.settings[preference_name] = value
    self.settings.store()

def load_user_preference(self, preference_name, default=None):
    """Load persisted state."""
    return self.settings.get(preference_name, default)
```

---

## Session State Patterns

### Pattern 1: Stateful List Selection

User selects an item from a list and you need to remember which.

```python
class NewsSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.articles = []
        self.selected_article = None

    def show_news_list(self):
        """Show list of news articles."""
        self.articles = self.fetch_news()

        self.gui.show_list(
            title="News",
            items=[a["title"] for a in self.articles]
        )

        # Store state for when user selects
        self.gui.set_context({
            "total_articles": len(self.articles),
            "selected_index": 0
        })

        # Listen for selection
        self.gui.register_handler(
            "news.article_selected",
            self.on_article_selected
        )

    def on_article_selected(self, message):
        """User selected an article."""
        index = message.data.get("selected", 0)
        self.selected_article = self.articles[index]

        # Update display to show selected article
        self.gui.show_generic(
            data={
                "title": self.selected_article["title"],
                "content": self.selected_article["body"],
                "source": self.selected_article["source"]
            }
        )
```

### Pattern 2: Multi-Page Workflow

User navigates through several pages, building up state.

```python
class SettingsWizard(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # State for the wizard flow
        self.wizard_state = {
            "step": 1,
            "username": "",
            "api_key": "",
            "notifications_enabled": True
        }

    def start_wizard(self):
        """Step 1: Ask for username."""
        self.wizard_state["step"] = 1
        self.gui.show_generic(
            data={
                "type": "text_input",
                "prompt": "Enter your username"
            }
        )

        self.gui.register_handler(
            "wizard.username_entered",
            self.on_username_entered
        )

    def on_username_entered(self, message):
        """Step 2: Confirm username, ask for API key."""
        username = message.data.get("value", "")
        self.wizard_state["username"] = username

        self.wizard_state["step"] = 2
        self.gui.show_generic(
            data={
                "type": "text_input",
                "prompt": "Enter your API key",
                "message": f"Confirmed: {username}"
            }
        )

        self.gui.register_handler(
            "wizard.api_key_entered",
            self.on_api_key_entered
        )

    def on_api_key_entered(self, message):
        """Step 3: Confirm and save."""
        api_key = message.data.get("value", "")
        self.wizard_state["api_key"] = api_key

        self.wizard_state["step"] = 3
        self.gui.show_generic(
            data={
                "type": "confirmation",
                "message": (
                    f"Username: {self.wizard_state['username']}\n"
                    f"API Key: {'*' * len(api_key)}\n"
                    "Is this correct?"
                )
            }
        )

        self.gui.register_handler(
            "wizard.confirmed",
            self.on_wizard_confirmed
        )

    def on_wizard_confirmed(self, message):
        """Save wizard state."""
        confirmed = message.data.get("confirmed", False)
        if confirmed:
            # Save to persistent settings
            self.settings["username"] = self.wizard_state["username"]
            self.settings["api_key"] = self.wizard_state["api_key"]
            self.settings.store()

            self.gui.show_notification(
                title="Setup Complete",
                body="Your settings have been saved"
            )
        else:
            # Restart wizard
            self.start_wizard()
```

### Pattern 3: Real-Time Updates

Update display without clearing it (faster than full page reload).

```python
class MusicPlayerSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_track = {}
        self.elapsed_time = 0

    def show_now_playing(self):
        """Show music player."""
        self.current_track = self.get_current_track()

        self.gui.show_music(
            title=self.current_track["title"],
            artist=self.current_track["artist"],
            album_art=self.current_track["image"],
            duration=self.current_track["duration"],
            elapsed=0
        )

        # Start updating elapsed time
        self.start_time_updates()

    def start_time_updates(self):
        """Update elapsed time every 500ms."""
        from threading import Timer

        def update_time():
            self.elapsed_time += 0.5

            # Update session instead of full page reload
            # This is much faster
            self.gui.set_context({
                "elapsed": self.elapsed_time,
                "remaining": self.current_track["duration"] - self.elapsed_time
            })

            # Schedule next update
            if self.elapsed_time < self.current_track["duration"]:
                timer = Timer(0.5, update_time)
                timer.daemon = True
                timer.start()

        update_time()
```

---

## Persistent State Patterns

### Pattern 1: Skill Settings

OVOS automatically saves skill settings to `~/.local/share/ovos/skills/<skill-id>/settings.json`.

```python
class WeatherSkill(OVOSSkill):
    def initialize(self):
        """Load settings on startup."""
        # Default location if not set
        self.location = self.settings.get(
            "default_location",
            "Berlin"
        )

    def handle_set_location(self, message):
        """User sets default location."""
        location = message.data.get("location")

        # Save to persistent settings
        self.settings["default_location"] = location
        self.settings.store()

        self.location = location
        self.speak_dialog("location_set", data={"location": location})

    def handle_weather_intent(self, message):
        """Show weather for default location."""
        weather = self.get_weather(self.location)
        self.gui.show_weather(**weather)
```

Settings file (`~/.local/share/ovos/skills/skill-weather.openvoiceos/settings.json`):

```json
{
  "default_location": "Berlin",
  "units": "metric",
  "show_forecast": true
}
```

### Pattern 2: Database Storage

For large data sets, use a database instead of settings.

```python
import sqlite3
from pathlib import Path

class PlaylistSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = Path(
            self.settings_path
        ) / "playlists.db"
        self.init_database()

    def init_database(self):
        """Create database on first run."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_date TIMESTAMP,
                tracks TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_playlist(self, name, tracks):
        """Save playlist to database."""
        import json

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO playlists (name, created_date, tracks)
            VALUES (?, datetime('now'), ?)
        """, (name, json.dumps(tracks)))

        conn.commit()
        conn.close()

    def load_playlists(self):
        """Load all playlists."""
        import json

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM playlists")
        playlists = [
            {"id": row[0], "name": row[1]}
            for row in cursor.fetchall()
        ]

        conn.close()
        return playlists
```

---

## State Cleanup

### Cleanup on Shutdown

Always clean up state when the skill stops.

```python
class MySkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_timer = None
        self.session_handlers = []

    def shutdown(self):
        """Called when skill stops."""
        # Cancel any running timers
        if self.background_timer:
            self.background_timer.cancel()

        # Unregister handlers
        for handler_name in self.session_handlers:
            self.gui.remove_handler(handler_name)

        # Clear session data
        self.gui.clear_context()

        # Close databases
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
```

### Clear Old Session Data

Clean up when starting a new session.

```python
def start_new_session(self):
    """Start fresh session, clearing old data."""
    # Remove old handlers
    for handler_name in ["action1", "action2", "action3"]:
        self.gui.remove_handler(handler_name)

    # Clear context
    self.gui.clear_context()

    # Reset instance state
    self.current_page = None
    self.selected_item = None
```

---

## Best Practices

### 1. Use Instance Variables for Skill Session State

```python
class MySkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Instance state — persists during skill session
        self.user_selections = {}
        self.context_data = {}
```

### 2. Use Settings for User Preferences

```python
# ✅ Good: Save user preferences
self.settings["preferred_language"] = "en"
self.settings.store()

# ❌ Bad: Don't store session data in settings
# (will accumulate and slow things down)
self.settings["scroll_position"] = 150
self.settings.store()
```

### 3. Use Session Context for Temporary State

```python
# ✅ Good: Temporary state
self.gui.set_context({
    "current_selection": 5,
    "highlighted": True
})

# ❌ Bad: Don't use session for long-term data
# (lost when page changes)
```

### 4. Clean Up on Shutdown

```python
def shutdown(self):
    """Always cleanup."""
    self.gui.clear_context()
    # Close connections
    # Cancel timers
```

### 5. Don't Store Sensitive Data in Logs

```python
# ❌ Bad: Password in logs
self.log.info(f"User password: {password}")

# ✅ Good: Only log that operation occurred
self.log.info("User credentials saved")
```

---

## Troubleshooting

### State Not Persisting Across Skill Restarts

**Problem**: Variables reset when skill is reloaded.

**Solution**: Use settings, not instance variables.

```python
# ❌ Bad: Lost on restart
self.playlist = []  # Cleared when skill stops

# ✅ Good: Persists
self.settings["playlist"] = []
self.settings.store()  # Load on initialize()
```

### State Accumulating Memory

**Problem**: Memory usage grows over time.

**Solution**: Implement cleanup.

```python
def initialize(self):
    # Clear old state from previous runs
    self.cache = {}
    self.timers = []

def shutdown(self):
    # Cancel all timers
    for timer in self.timers:
        timer.cancel()
```

### Session Data Lost Between Pages

**Problem**: Context doesn't survive page changes.

**Solution**: Use instance variables or settings.

```python
# Session context (temporary)
self.gui.set_context({"temp_selection": 5})  # Lost when page changes

# Instance variable (survives page changes)
self.current_selection = 5  # Survives as long as skill is running

# Settings (persistent)
self.settings["saved_selection"] = 5  # Survives skill restart
```

---

## See Also

- **[Core Concepts](concepts.md)** — Session data overview
- **[Skill GUI Development](skill-gui-development.md)** — Showing pages and handling events
- **[Skill Examples](skill-examples.md)** — Real working examples with state
