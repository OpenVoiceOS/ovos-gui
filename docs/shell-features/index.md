# Shell Features — First-Class GUI Extensions

Shell features are system-level GUI capabilities that enhance user experience and device control. They are now **part of the main OpenVoiceOS GUI specification** and should be supported by all adapters where appropriate for their platform.

These features were historically called "GUI extensions" but are now treated as integral to the GUI system, not optional plugins.

## Overview

Shell features cover four domains:

| Domain | Purpose | Example |
|--------|---------|---------|
| **Brightness** | Screen brightness and lighting control | Auto-dimming, night mode, manual brightness adjustment |
| **Color Scheme** | Theme and appearance customization | Dark/light theme, custom color schemes |
| **Notifications** | System notifications and alerts | Popup messages, toast notifications, status messages |
| **Widgets** | Custom UI components and displays | Clock, weather, music player, calendar |
| **Configuration** | Settings and preferences UI | Audio settings, network config, device settings |

## Message Types

All shell features communicate via standardized MessageBus messages. See `GUIMessageType` enum in `ovos_gui.message_types` for complete definitions.

### Brightness Control

```python
from ovos_gui import GUIMessageType

# Set brightness to 50%
bus.emit(Message(GUIMessageType.GUI_BRIGHTNESS_SET, {"brightness": 50}))

# Enable night mode
bus.emit(Message(GUIMessageType.GUI_BRIGHTNESS_NIGHT_MODE_SET, {"enabled": True}))

# Query current brightness
bus.emit(Message(GUIMessageType.GUI_BRIGHTNESS_GET))
```

Messages:
- `gui.brightness.set` — Change screen brightness (0-100)
- `gui.brightness.get` — Query current brightness
- `gui.brightness.auto_dim.set` — Enable/disable automatic dimming
- `gui.brightness.night_mode.set` — Enable/disable night mode

### Color Scheme Management

```python
# Set color scheme
bus.emit(Message(GUIMessageType.GUI_COLOR_SCHEME_SET, {"scheme": "dark"}))

# Get available schemes
bus.emit(Message(GUIMessageType.GUI_COLOR_SCHEME_GET))
```

Messages:
- `gui.color_scheme.set` — Change theme or color scheme
- `gui.color_scheme.get` — List available schemes

**Recommended Schemes:**
- `light` — High contrast light theme
- `dark` — High contrast dark theme
- `high_contrast` — Accessibility mode

### Notifications

```python
# Display a notification
bus.emit(Message(GUIMessageType.GUI_NOTIFICATION_SET, {
    "title": "Update Available",
    "message": "A new version is available",
    "duration": 5000,  # milliseconds
    "type": "info"  # info|warning|error|success
}))

# Clear active notifications
bus.emit(Message(GUIMessageType.GUI_NOTIFICATION_CLEAR))
```

Messages:
- `gui.notification.set` — Show a notification
- `gui.notification.clear` — Dismiss all notifications

**Notification Types:**
- `info` — Informational message (blue/neutral color)
- `warning` — Warning that requires attention (yellow/orange)
- `error` — Error or critical issue (red)
- `success` — Operation completed successfully (green)

### Custom Widgets

```python
# Display a custom widget
bus.emit(Message(GUIMessageType.GUI_WIDGET_DISPLAY, {
    "widget_id": "skill_weather.temp_display",
    "config": {
        "temperature": 22,
        "unit": "C",
        "location": "Berlin"
    }
}))

# Remove widget
bus.emit(Message(GUIMessageType.GUI_WIDGET_REMOVE, {"widget_id": "skill_weather.temp_display"}))
```

Messages:
- `gui.widget.display` — Create or update a widget
- `gui.widget.remove` — Remove a widget from display

**Widget Lifecycle:**
1. Display message creates or updates widget
2. Widget remains on screen until remove message
3. Adapter handles rendering based on `widget_id` and config

### Configuration UI

```python
# Get available config modules
bus.emit(Message(GUIMessageType.GUI_CONFIG_LIST_GET))

# Get configuration for a module
bus.emit(Message(GUIMessageType.GUI_CONFIG_GET, {"module": "audio"}))

# Update configuration
bus.emit(Message(GUIMessageType.GUI_CONFIG_SET, {
    "module": "audio",
    "config": {
        "default_tts": "espeak",
        "default_stt": "google"
    }
}))
```

Messages:
- `gui.config.list.get` — Get available config modules
- `gui.config.get` — Retrieve config for a module
- `gui.config.set` — Update config for a module

## Adapter Implementation

Adapters SHOULD support shell features to the extent their platform allows:

| Adapter | Brightness | Color Scheme | Notifications | Widgets | Config |
|---------|------------|--------------|----------------|---------|--------|
| **Qt6 (Desktop)** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Web** | ✅ Full | ✅ Full | ✅ Full | ⚠️ Limited | ⚠️ Limited |
| **TUI (Terminal)** | ⚠️ Limited | ✅ Limited | ⚠️ Basic | ❌ None | ✅ Text |
| **Smart Display** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Limited |

**Legend:**
- ✅ Full — Complete implementation with all features
- ⚠️ Limited — Partial implementation (e.g., web notifications are OS-dependent)
- ❌ None — Not applicable to this platform

### Handling Unsupported Features

Adapters that don't support a feature SHOULD:

1. **Log gracefully:** `LOG.debug("Brightness not supported on TUI adapter")`
2. **Silently ignore:** Don't crash; just don't render the feature
3. **Provide fallback:** If possible, offer degraded functionality (e.g., text-based config UI)

## Skill Usage

Skills can send shell feature messages to enhance user experience:

```python
from mycroft.skills.context import adds_context
from ovos_gui import GUIMessageType

class WeatherSkill(OVOSSkill):
    def handle_weather(self, message):
        # Show weather via template
        self.gui.show_weather(
            current_temp=22,
            condition="Sunny",
            location="Berlin"
        )

        # Optional: Adjust brightness based on weather
        if condition == "Clear":
            # Bright for sunny weather
            self.bus.emit(Message(GUIMessageType.GUI_BRIGHTNESS_SET, {"brightness": 90}))
        elif condition == "Rainy":
            # Darker theme for rainy weather
            self.bus.emit(Message(GUIMessageType.GUI_COLOR_SCHEME_SET, {"scheme": "dark"}))
```

## Configuration

Shell features are configured in `mycroft.conf`:

```json
{
  "gui": {
    "shell_features": {
      "brightness_control": true,
      "color_scheme_management": true,
      "notifications": true,
      "widgets": true,
      "configuration_ui": true
    }
  }
}
```

## Status Events

All adapters receive status events and can use them to update shell feature state:

| Event | Use Case |
|-------|----------|
| `mycroft.recognizer_loop.wake_word` | Show listening indicator; adjust brightness |
| `mycroft.recognizer_loop.record_begin` | Display recording UI; pause other animations |
| `mycroft.audio_output.start` | Show audio playing indicator |
| `mycroft.skill.handler.start` | Disable certain UI controls during skill execution |

See `[ovos-gui: docs/adapter-development/bus-protocol.md]` for complete list.

## See Also

- `[ovos-gui: ovos_gui/message_types.py]` — `GUIMessageType` enum definition
- `[ovos-gui: docs/adapter-development/bus-protocol.md]` — Full MessageBus protocol reference
- `[ovos-gui: docs/skill-development/templates.md]` — Template-based skill display
