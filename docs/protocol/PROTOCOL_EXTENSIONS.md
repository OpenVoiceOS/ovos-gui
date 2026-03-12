# OVOS GUI Protocol Extensions — Shell Features

**Date**: 2026-03-12
**Source**: `ovos-legacy-mycroft-gui-plugin/docs/PROTOCOL_EXTENSIONS.md`
**Status**: ✅ Implemented in adapter and Qt client

## Overview

This document extends the [standard OVOS GUI protocol](./protocol.md) with standardized message types for shell features (brightness, color schemes, notifications, widgets, configuration UI).

These extensions unify all GUI communication—both template rendering and shell features—over a single WebSocket protocol.

## Table of Contents

- [Design Rationale](#design-rationale)
- [Brightness Control](#brightness-control)
- [Color Scheme Management](#color-scheme-management)
- [Notifications](#notifications)
- [Widgets](#widgets)
- [Configuration UI](#configuration-ui)
- [Implementation Status](#implementation-status)

---

## Design Rationale

### The Problem

Previous architecture had shell features (brightness, colors, notifications) implemented as MessageBus listeners in the adapter with no way for WebSocket-only Qt clients to trigger them.

### The Solution

Extend the WebSocket protocol with new message types prefixed with `gui.*` to handle shell features. This creates a unified bidirectional protocol where:

- **Client → Server**: User actions (brightness slider, color picker, config changes)
- **Server → Client**: System updates (theme changes, notifications, widgets)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    OVOS Core (Python)                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │ BrightnessManager, ColorManager, WidgetManager    │  │
│  │ (listen to MessageBus events from other services) │  │
│  └───────────────────────────────────────────────────┘  │
│                        ↑ ↓ MessageBus                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │ GUI Adapter (Tornado WebSocket Server)            │  │
│  │ - Routes OVOS templates to Qt clients             │  │
│  │ - Bridges MessageBus ↔ WebSocket for shell features
│  └───────────────────────────────────────────────────┘  │
│                        ↑ ↓ WebSocket                     │
└─────────────────────────────────────────────────────────┘
                          ↑ ↓
┌─────────────────────────────────────────────────────────┐
│              mycroft-gui-qt6 (C++ Client)                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ShellFeatureController (QML Singleton)            │  │
│  │ - Receives shell feature protocol messages        │  │
│  │ - Emits QML signals for UI components            │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Brightness Control

### gui.brightness.set

**Direction**: Client → Server

**Purpose**: User adjusts brightness slider

**Format**:
```json
{
    "type": "gui.brightness.set",
    "data": {
        "brightness": 75
    }
}
```

**Valid range**: 0-100 (percent)

**Server action**:
- Update BrightnessManager
- Emit `phal.brightness.control.auto.dim.update` to OVOS services

---

### gui.brightness.get

**Direction**: Client → Server

**Purpose**: Request current brightness level

**Format**:
```json
{
    "type": "gui.brightness.get"
}
```

**Server response**:
```json
{
    "type": "gui.brightness.get.response",
    "data": {
        "brightness": 85
    }
}
```

---

### gui.brightness.auto_dim.set

**Direction**: Client → Server

**Purpose**: Enable/disable auto-dimming after inactivity

**Format**:
```json
{
    "type": "gui.brightness.auto_dim.set",
    "data": {
        "auto_dim": true,
        "timeout_seconds": 60
    }
}
```

**Server action**:
- Update BrightnessManager
- Emit `speaker.extension.display.set.auto.dim` bus message

---

### gui.brightness.night_mode.set

**Direction**: Client → Server

**Purpose**: Enable/disable automatic dimming at sunset, brightening at sunrise

**Format**:
```json
{
    "type": "gui.brightness.night_mode.set",
    "data": {
        "auto_nightmode": true,
        "sunrise_time": "auto",
        "sunset_time": "auto"
    }
}
```

**Parameters**:
- `auto_nightmode` (bool): Enable night mode
- `sunrise_time` (str): "auto" (calculate from location) or "HH:MM" (24-hour format)
- `sunset_time` (str): "auto" or "HH:MM"

**Server action**:
- Update BrightnessManager
- Emit `speaker.extension.display.set.auto.nightmode` bus message

---

## Color Scheme Management

### gui.color_scheme.set

**Direction**: Client ↔ Server (bidirectional)

**Purpose**: Create or update color theme

**Format**:
```json
{
    "type": "gui.color_scheme.set",
    "data": {
        "theme_name": "Ocean Blue",
        "primaryColor": "#0066CC",
        "secondaryColor": "#00CCFF",
        "textColor": "#FFFFFF",
        "accentColor": "#FFAA00"
    }
}
```

**Valid colors**: Hex format (e.g., `#FF6B6B`)

**Server action**:
- Save to `~/.local/share/OVOS/ColorSchemes/{theme_name}.json`
- Emit `ovos.shell.gui.color.scheme.generated` bus message

---

### gui.color_scheme.get

**Direction**: Client → Server

**Purpose**: Request current active theme

**Format**:
```json
{
    "type": "gui.color_scheme.get"
}
```

**Server response**:
```json
{
    "type": "gui.color_scheme.get.response",
    "data": {
        "name": "Ocean Blue",
        "primaryColor": "#0066CC",
        "secondaryColor": "#00CCFF",
        "textColor": "#FFFFFF",
        "accentColor": "#FFAA00"
    }
}
```

---

## Notifications

### gui.notification.set

**Direction**: Server → Client

**Purpose**: Display notification alert

**Format**:
```json
{
    "type": "gui.notification.set",
    "data": {
        "title": "New Message",
        "body": "You have a new email",
        "icon": "/path/to/icon.png",
        "timeout": 5000,
        "notification_id": "msg_123"
    }
}
```

**Parameters**:
- `title` (str): Notification title
- `body` (str): Notification message
- `icon` (str): Path or URL to icon (optional)
- `timeout` (int): Milliseconds before auto-dismiss (optional, default 5000)
- `notification_id` (str): Unique identifier (optional)

---

### gui.notification.clear

**Direction**: Client → Server

**Purpose**: User dismisses notification

**Format**:
```json
{
    "type": "gui.notification.clear",
    "data": {
        "notification_id": "msg_123"
    }
}
```

**Server action**:
- Remove notification from WidgetManager queue
- Emit `ovos.notification.api.pop.clear` bus message

---

## Widgets

### gui.widget.display

**Direction**: Server → Client

**Purpose**: Display custom widget on screen

**Format**:
```json
{
    "type": "gui.widget.display",
    "data": {
        "widget_id": "weather",
        "widget_type": "weather_card",
        "position": "home",
        "data": {
            "temp": 72,
            "condition": "sunny",
            "location": "San Francisco"
        }
    }
}
```

---

### gui.widget.remove

**Direction**: Client ↔ Server

**Purpose**: Remove widget from display

**Format**:
```json
{
    "type": "gui.widget.remove",
    "data": {
        "widget_id": "weather"
    }
}
```

---

## Configuration UI

### gui.config.list.get

**Direction**: Client → Server

**Purpose**: Request available configuration groups

**Format**:
```json
{
    "type": "gui.config.list.get"
}
```

**Server response**:
```json
{
    "type": "gui.config.list.get.response",
    "data": {
        "groups": [
            {"group": "mycroft", "label": "Core Settings"},
            {"group": "audio", "label": "Audio Settings"}
        ]
    }
}
```

---

### gui.config.get

**Direction**: Client → Server

**Purpose**: Request configuration for a specific group

**Format**:
```json
{
    "type": "gui.config.get",
    "data": {
        "group_name": "audio"
    }
}
```

**Server response**:
```json
{
    "type": "gui.config.get.response",
    "data": {
        "group_name": "audio",
        "settings_metadata": {
            "brightness": {
                "label": "Brightness",
                "value": 85,
                "type": "int"
            }
        }
    }
}
```

---

### gui.config.set

**Direction**: Client → Server

**Purpose**: User saves configuration changes

**Format**:
```json
{
    "type": "gui.config.set",
    "data": {
        "group_name": "audio",
        "values": {
            "brightness": 75
        }
    }
}
```

**Server action**:
- Update mycroft.conf via ConfigUIManager
- Emit `ovos.phal.configuration.provider.set` bus message

---

## Implementation Status

### ✅ Completed

**Adapter** (`ovos-legacy-mycroft-gui-plugin`):
- Protocol extensions designed and documented
- WebSocket handlers implemented for all message types
- Manager helper methods added for synchronous access
- Ready for Qt client integration

**Qt Client** (`mycroft-gui-qt6`):
- GUIBusMessages extended with shell feature types
- ShellFeatureController class implemented (QML singleton)
- Message routing in MycroftController
- QML signals for UI integration

### 🔲 TODO

**ovos-gui** (this repository):
- Whitelist new message types (if validation required)
- Update main protocol documentation
- Add tests for protocol extension messages

**Documentation**:
- Add QML integration guide for shell features
- Create migration guide from old shell-companion approach
- Add examples for each shell feature type

---

## Message Type Reference

| Message Type | Direction | Purpose | Handler |
|---|---|---|---|
| `gui.brightness.set` | C→S | Set brightness level | BrightnessManager |
| `gui.brightness.get` | C→S | Get current brightness | BrightnessManager |
| `gui.brightness.get.response` | S→C | Response with brightness | ShellFeatureController |
| `gui.brightness.auto_dim.set` | C→S | Toggle auto-dim | BrightnessManager |
| `gui.brightness.night_mode.set` | C→S | Toggle night mode | BrightnessManager |
| `gui.color_scheme.set` | C↔S | Save color theme | ColorManager |
| `gui.color_scheme.get` | C→S | Get active theme | ColorManager |
| `gui.color_scheme.get.response` | S→C | Response with theme | ShellFeatureController |
| `gui.notification.set` | S→C | Display notification | ShellFeatureController |
| `gui.notification.clear` | C→S | Dismiss notification | WidgetManager |
| `gui.widget.display` | S→C | Display widget | ShellFeatureController |
| `gui.widget.remove` | C↔S | Remove widget | WidgetManager |
| `gui.config.list.get` | C→S | Get config groups | ConfigUIManager |
| `gui.config.list.get.response` | S→C | Response with groups | ShellFeatureController |
| `gui.config.get` | C→S | Get group config | ConfigUIManager |
| `gui.config.get.response` | S→C | Response with config | ShellFeatureController |
| `gui.config.set` | C→S | Save config changes | ConfigUIManager |

---

## Related Documentation

- [Main Protocol Specification](./protocol.md)
- [Adapter Development Guide](../adapter-development/index.md)
- [ovos-legacy-mycroft-gui-plugin PROTOCOL_EXTENSIONS.md](https://github.com/OpenVoiceOS/ovos-legacy-mycroft-gui-plugin/blob/dev/docs/PROTOCOL_EXTENSIONS.md)
- [mycroft-gui-qt6 Shell Feature Implementation](https://github.com/OpenVoiceOS/mycroft-gui-qt6/blob/dev/import/shellfeaturecontroller.h)
