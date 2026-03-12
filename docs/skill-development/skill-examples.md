# Skill Examples — Real-World GUI Patterns

Copy-paste examples showing real skills with GUI integration.

---

## Example 1: Simple Weather Skill

Shows current weather and next-day forecast.

```python
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder
import requests

class WeatherSkill(OVOSSkill):
    """Display weather information."""

    def initialize(self):
        """Setup event handlers."""
        self.gui.register_handler(
            "weather.next_day",
            self.on_next_day_request
        )
        self.gui.register_handler(
            "weather.location_changed",
            self.on_location_changed
        )

    @intent_handler(
        IntentBuilder("CurrentWeather")
        .require("weather")
        .require("current")
    )
    def handle_current_weather(self, message):
        """Show current weather."""
        location = message.data.get("location", "Berlin")
        weather_data = self.get_weather(location)

        self.gui.show_weather(
            current_temp=weather_data["temp"],
            min_temp=weather_data["min_temp"],
            max_temp=weather_data["max_temp"],
            condition=weather_data["condition"],
            location=location,
            icon=weather_data["icon"],
            humidity=weather_data.get("humidity"),
            wind_speed=weather_data.get("wind_speed")
        )

        # Also speak the weather
        self.speak_dialog(
            "weather_template",
            data={
                "temp": weather_data["temp"],
                "condition": weather_data["condition"],
                "location": location
            }
        )

    @intent_handler(
        IntentBuilder("ForecastWeather")
        .require("weather")
        .require("forecast")
    )
    def handle_forecast(self, message):
        """Show weather forecast."""
        location = message.data.get("location", "Berlin")
        forecast_data = self.get_forecast(location)

        self.gui.show_generic(
            data={
                "title": f"Forecast for {location}",
                "forecast": [
                    {
                        "day": day,
                        "high": temps["high"],
                        "low": temps["low"],
                        "condition": temps["condition"]
                    }
                    for day, temps in forecast_data.items()
                ]
            }
        )

        self.speak_dialog("forecast_template")

    def on_next_day_request(self, message):
        """Handle user request to see next day."""
        location = message.data.get("location", "Berlin")
        self.handle_forecast(message)

    def on_location_changed(self, message):
        """Handle location change from UI."""
        location = message.data.get("location")
        self.log.info(f"Location changed to {location}")
        self.handle_current_weather(message)

    def get_weather(self, location):
        """Fetch weather from API."""
        # This is a mock implementation
        return {
            "temp": 22,
            "min_temp": 18,
            "max_temp": 26,
            "condition": "Partly Cloudy",
            "icon": "cloud.png",
            "humidity": 65,
            "wind_speed": 15
        }

    def get_forecast(self, location):
        """Fetch forecast."""
        return {
            "Monday": {"high": 24, "low": 18, "condition": "Sunny"},
            "Tuesday": {"high": 22, "low": 16, "condition": "Cloudy"},
            "Wednesday": {"high": 20, "low": 14, "condition": "Rainy"}
        }


def create_skill():
    return WeatherSkill()
```

---

## Example 2: Music Player Skill with Controls

Shows now playing with prev/next buttons.

```python
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder
import json

class MusicPlayerSkill(OVOSSkill):
    """Play music with GUI controls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.playlist = []
        self.current_index = 0
        self.is_playing = False

    def initialize(self):
        """Setup event handlers."""
        self.gui.register_handler(
            "music.next_button",
            self.handle_next
        )
        self.gui.register_handler(
            "music.previous_button",
            self.handle_previous
        )
        self.gui.register_handler(
            "music.play_pause_button",
            self.handle_play_pause
        )
        self.gui.register_handler(
            "music.seek",
            self.handle_seek
        )

    @intent_handler(
        IntentBuilder("PlayMusic")
        .require("play")
        .require("music")
        .optionally("query")
    )
    def handle_play_music(self, message):
        """Play music."""
        query = message.data.get("query", "")
        self.playlist = self.search_music(query)
        self.current_index = 0
        self.is_playing = True

        self.play_current_song()

    def play_current_song(self):
        """Display and play current song."""
        if not self.playlist:
            self.speak("No songs to play")
            return

        song = self.playlist[self.current_index]

        self.gui.show_music(
            title=song["title"],
            artist=song["artist"],
            album=song["album"],
            album_art=song["image_url"],
            duration=song["duration"],
            elapsed=0,  # Start from beginning
            playlist_size=len(self.playlist),
            playlist_index=self.current_index,
            support_next=True,
            support_previous=True,
            can_stream=True
        )

        # Play audio (mock)
        self.log.info(f"Playing: {song['title']} by {song['artist']}")

    def handle_next(self, message):
        """Play next song."""
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.play_current_song()
            self.speak("Next song")

    def handle_previous(self, message):
        """Play previous song."""
        if self.current_index > 0:
            self.current_index -= 1
            self.play_current_song()
            self.speak("Previous song")

    def handle_play_pause(self, message):
        """Toggle playback."""
        self.is_playing = not self.is_playing
        status = "playing" if self.is_playing else "paused"
        self.speak(f"Music {status}")

    def handle_seek(self, message):
        """Handle seek requests."""
        position = message.data.get("position", 0)
        self.log.info(f"Seeking to {position} seconds")

    def search_music(self, query):
        """Search for music."""
        # Mock implementation
        return [
            {
                "title": "Bohemian Rhapsody",
                "artist": "Queen",
                "album": "A Night at the Opera",
                "duration": 354,
                "image_url": "https://example.com/queen.jpg"
            },
            {
                "title": "Stairway to Heaven",
                "artist": "Led Zeppelin",
                "album": "Led Zeppelin IV",
                "duration": 482,
                "image_url": "https://example.com/ledzep.jpg"
            },
            {
                "title": "Hotel California",
                "artist": "Eagles",
                "album": "Hotel California",
                "duration": 391,
                "image_url": "https://example.com/eagles.jpg"
            }
        ]


def create_skill():
    return MusicPlayerSkill()
```

---

## Example 3: News Reader with List Selection

Shows news articles and reads selected one.

```python
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder

class NewsSkill(OVOSSkill):
    """Read news articles."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.articles = []

    def initialize(self):
        """Setup event handlers."""
        self.gui.register_handler(
            "news.article_selected",
            self.on_article_selected
        )

    @intent_handler(
        IntentBuilder("ReadNews")
        .require("read")
        .require("news")
        .optionally("category")
    )
    def handle_read_news(self, message):
        """Display news articles."""
        category = message.data.get("category", "general")
        self.articles = self.fetch_news(category)

        # Show list of articles
        articles_list = [
            article["title"]
            for article in self.articles
        ]

        self.gui.show_list(
            title=f"News: {category.capitalize()}",
            items=articles_list
        )

        self.speak_dialog(
            "showing_news",
            data={"category": category}
        )

    def on_article_selected(self, message):
        """Handle article selection."""
        selected_index = message.data.get("selected", 0)

        if selected_index < len(self.articles):
            article = self.articles[selected_index]

            # Show article details
            self.gui.show_generic(
                data={
                    "title": article["title"],
                    "source": article["source"],
                    "image": article["image"],
                    "summary": article["summary"],
                    "published": article["published"]
                }
            )

            # Read article aloud
            self.speak(article["summary"])

    def fetch_news(self, category):
        """Fetch news articles."""
        # Mock implementation
        return [
            {
                "title": "Breaking News: Important Announcement",
                "source": "BBC News",
                "image": "https://example.com/news1.jpg",
                "summary": "This is an important news story...",
                "published": "2 minutes ago"
            },
            {
                "title": "Tech Giant Launches New Product",
                "source": "Tech Crunch",
                "image": "https://example.com/news2.jpg",
                "summary": "A major technology company announced...",
                "published": "1 hour ago"
            },
            {
                "title": "Sports Update: Team Wins Championship",
                "source": "ESPN",
                "image": "https://example.com/news3.jpg",
                "summary": "The local team has won the championship...",
                "published": "3 hours ago"
            }
        ]


def create_skill():
    return NewsSkill()
```

---

## Example 4: Timer with Real-Time Updates

Shows countdown timer with progress visualization.

```python
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder
from threading import Timer
import time

class TimerSkill(OVOSSkill):
    """Countdown timer with GUI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer = None
        self.remaining = 0
        self.duration = 0

    def initialize(self):
        """Setup event handlers."""
        self.gui.register_handler(
            "timer.stop",
            self.handle_stop_timer
        )
        self.gui.register_handler(
            "timer.pause",
            self.handle_pause
        )

    @intent_handler(
        IntentBuilder("SetTimer")
        .require("set")
        .require("timer")
        .require("duration")
    )
    def handle_set_timer(self, message):
        """Set a timer."""
        duration_seconds = message.data.get("duration", 300)  # 5 minutes default
        self.duration = duration_seconds
        self.remaining = duration_seconds

        self.gui.show_generic(
            data={
                "type": "timer",
                "title": "Timer",
                "duration": duration_seconds,
                "remaining": self.remaining,
                "progress": 100  # 100% at start
            }
        )

        self.speak_dialog(
            "timer_set",
            data={"duration": duration_seconds // 60}
        )

        self.start_countdown()

    def start_countdown(self):
        """Start the countdown timer."""
        if self.timer:
            self.timer.cancel()

        self.update_timer()

    def update_timer(self):
        """Update timer display every second."""
        if self.remaining > 0:
            self.remaining -= 1

            # Calculate progress (0-100)
            progress = int(
                (self.remaining / self.duration) * 100
                if self.duration > 0 else 0
            )

            # Update GUI
            self.gui.set_context({
                "remaining": self.remaining,
                "progress": progress,
                "formatted_time": self.format_time(self.remaining)
            })

            # Schedule next update
            self.timer = Timer(1.0, self.update_timer)
            self.timer.daemon = True
            self.timer.start()
        else:
            # Timer finished
            self.on_timer_finished()

    def on_timer_finished(self):
        """Called when timer reaches zero."""
        self.gui.show_notification(
            title="Timer Finished",
            body="Your timer has completed"
        )
        self.speak("Your timer is done")

    def handle_stop_timer(self, message):
        """Stop the timer."""
        if self.timer:
            self.timer.cancel()
        self.speak("Timer stopped")

    def handle_pause(self, message):
        """Pause the timer."""
        if self.timer:
            self.timer.cancel()
        self.speak("Timer paused")

    @staticmethod
    def format_time(seconds):
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def shutdown(self):
        """Cleanup when skill stops."""
        if self.timer:
            self.timer.cancel()


def create_skill():
    return TimerSkill()
```

---

## Example 5: Calculator with Session State

Shows calculator with persistent input state.

```python
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder

class CalculatorSkill(OVOSSkill):
    """Simple calculator."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display = "0"
        self.operator = None
        self.previous = None

    def initialize(self):
        """Setup event handlers."""
        self.gui.register_handler(
            "calc.number_pressed",
            self.on_number_pressed
        )
        self.gui.register_handler(
            "calc.operator_pressed",
            self.on_operator_pressed
        )
        self.gui.register_handler(
            "calc.equals_pressed",
            self.on_equals_pressed
        )
        self.gui.register_handler(
            "calc.clear_pressed",
            self.on_clear_pressed
        )

    @intent_handler(
        IntentBuilder("Calculate")
        .require("calculate")
    )
    def handle_calculate(self, message):
        """Show calculator."""
        self.show_calculator()

    def show_calculator(self):
        """Display calculator UI."""
        self.gui.show_generic(
            data={
                "type": "calculator",
                "display": self.display,
                "buttons": [
                    [7, 8, 9, "/"],
                    [4, 5, 6, "*"],
                    [1, 2, 3, "-"],
                    [0, ".", "=", "+"]
                ]
            }
        )

        # Update session state
        self.gui.set_context({
            "display": self.display
        })

    def on_number_pressed(self, message):
        """Handle number button press."""
        number = message.data.get("number")

        if self.display == "0":
            self.display = str(number)
        else:
            self.display += str(number)

        self.show_calculator()

    def on_operator_pressed(self, message):
        """Handle operator button press."""
        operator = message.data.get("operator")
        self.operator = operator
        self.previous = float(self.display)
        self.display = "0"

    def on_equals_pressed(self, message):
        """Calculate result."""
        if self.operator and self.previous is not None:
            current = float(self.display)

            if self.operator == "+":
                result = self.previous + current
            elif self.operator == "-":
                result = self.previous - current
            elif self.operator == "*":
                result = self.previous * current
            elif self.operator == "/":
                result = self.previous / current if current != 0 else 0
            else:
                result = current

            self.display = str(int(result) if result == int(result) else result)
            self.operator = None
            self.previous = None

        self.show_calculator()

    def on_clear_pressed(self, message):
        """Clear calculator."""
        self.display = "0"
        self.operator = None
        self.previous = None
        self.show_calculator()


def create_skill():
    return CalculatorSkill()
```

---

## Example 6: Settings Form

Shows settings with text inputs and toggles.

```python
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder

class SettingsSkill(OVOSSkill):
    """Manage skill settings."""

    @intent_handler(
        IntentBuilder("OpenSettings")
        .require("open")
        .require("settings")
    )
    def handle_open_settings(self, message):
        """Show settings form."""
        self.gui.show_generic(
            data={
                "type": "settings_form",
                "title": "Skill Settings",
                "fields": [
                    {
                        "name": "username",
                        "label": "Username",
                        "type": "text",
                        "value": self.settings.get("username", "")
                    },
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "type": "password",
                        "value": self.settings.get("api_key", "")
                    },
                    {
                        "name": "notifications_enabled",
                        "label": "Enable Notifications",
                        "type": "toggle",
                        "value": self.settings.get("notifications_enabled", True)
                    },
                    {
                        "name": "update_frequency",
                        "label": "Update Frequency (minutes)",
                        "type": "number",
                        "value": self.settings.get("update_frequency", 60)
                    }
                ]
            }
        )

        self.gui.register_handler(
            "settings.save",
            self.on_settings_saved
        )

    def on_settings_saved(self, message):
        """Handle settings save."""
        for field_name, value in message.data.items():
            self.settings[field_name] = value

        self.gui.show_notification(
            title="Settings Saved",
            body="Your settings have been updated"
        )
        self.speak("Settings saved")


def create_skill():
    return SettingsSkill()
```

---

## Tips for Real Skills

1. **Always provide voice feedback** in addition to GUI
2. **Test without an adapter** — have text fallbacks
3. **Handle rapid interactions** — debounce button clicks
4. **Cache API results** — don't spam external services
5. **Clean up handlers** in `shutdown()` method
6. **Log events for debugging** — use `self.log.info()`
7. **Use session state** for temporary UI updates (faster than re-rendering)
8. **Test on multiple adapters** — Qt5, web, headless

---

## See Also

- **[Skill GUI Development](skill-gui-development.md)** — Complete API reference
- **[Templates.md](templates.md)** — All 21 templates
- **[Testing GUI](testing-gui.md)** — Unit test your GUI features
- **[Advanced: Session State](advanced-state.md)** — Persistent data management
