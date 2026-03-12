# OVOS GUI Service Protocol

Complete specification for GUI communication between ovos-gui and connected clients.

This document covers both **core GUI rendering** and **shell feature extensions** in a unified protocol.

**See also:** [SESSION_AND_SITE_ID_DESIGN.md](../SESSION_AND_SITE_ID_DESIGN.md) for comprehensive multi-session architecture.

## Quick Reference: Sessions and Routing

- **`session_id`** — Unique identifier for a GUI client or screen. Defaults to `"default"` for on-device.
- **`site_id`** — Unique identifier for a physical location. Groups multiple screens that share state.
- **Message routing:** Include `__session_id` or `__site_id` in message data to target specific client(s).
- **Filtering rule:** GUI clients only receive messages for their own `session_id` (or matching `site_id`).

## Table of Contents

### Core GUI Protocol
- [CONNECTION - mycroft.gui.connected](#connection---mycroftguiconnected)
- [SESSION AND ROUTING](#session-and-routing)
- [NAMESPACES](#namespaces)
  * [Active Skills - mycroft.system.active_skills](#active-skills---mycroftsystemactive-skills)
- [PAGES - mycroft.gui.list.xxx](#pages---mycroftguilistxxx)
  * [Insert new page at position](#insert-new-page-at-position)
  * [Move pages within the list](#move-pages-within-the-list)
  * [Remove pages from the list](#remove-pages-from-the-list)
- [EVENTS - mycroft.events.triggered](#events---mycrofteventstriggered)
  * [SPECIAL EVENT: page_gained_focus](#special-event--page-gained-focus)
- [SKILL DATA - mycroft.session.xxx](#skill-data---mycroftsessionxxx)
  * [Sets a new key/value in the sessionData dictionary](#sets-a-new-key-value-in-the-sessiondata-dictionary)
  * [Deletes a key/value pair from the sessionData dictionary](#deletes-a-key-value-pair-from-the-sessiondata-dictionary)
  * [Lists](#lists)
    + [Inserts new items at position](#inserts-new-items-at-position)
    + [Updates item values starting at the given position, as many items as there are in the array](#updates-item-values-starting-at-the-given-position--as-many-items-as-there-are-in-the-array)
    + [Move items within the list](#move-items-within-the-list)
    + [Remove items from the list](#remove-items-from-the-list)

### Shell Feature Extensions (Protocol Extensions)
- [SHELL FEATURES OVERVIEW](#shell-features-overview)
- [BRIGHTNESS CONTROL](#brightness-control)
- [COLOR SCHEME MANAGEMENT](#color-scheme-management)
- [NOTIFICATIONS](#notifications)
- [WIDGETS](#widgets)
- [CONFIGURATION UI](#configuration-ui)


# CONNECTION - mycroft.gui.connected

On connection, GUI clients announce themselves with session and site information.

This is an extension by OVOS to the [original mycroft protocol](https://github.com/MycroftAI/mycroft-gui/blob/master/transportProtocol.md)

## Basic Connection (Backward Compatible)

```javascript
{
    "type": "mycroft.gui.connected",
    "gui_id": "unique_identifier_provided_by_client"
}
```

When `session_id` and `site_id` are omitted, client defaults to `session_id="default"` (on-device).

## Connection with Session and Site Information

```javascript
{
    "type": "mycroft.gui.connected",
    "gui_id": "unique_identifier_provided_by_client",
    "session_id": "living_room_tablet",  // Optional: custom session ID
    "site_id": "kitchen"                 // Optional: location/site identifier
}
```

**Fields:**
- `gui_id` (string, required) — Unique identifier for this client (UUID or MAC address)
- `session_id` (string, optional) — Session identifier. Defaults to `"default"` if omitted.
- `site_id` (string, optional) — Site/location identifier for multi-location deployments.

---

# SESSION AND ROUTING

## Message Routing Overview

ovos-gui routes GUI state messages to specific `session_id` or `site_id` based on message content.

| Target Type | How Specified | Recipients |
|---|---|---|
| **Specific Session** | `__session_id` in message data | Only clients with matching `session_id` |
| **Specific Site (Sync Mode)** | `__site_id` in message data | All clients with matching `site_id` (if enabled) |
| **Default (Legacy)** | Neither specified | Clients with `session_id="default"` only |

## Routing Rules

**Rule 1: Session-Targeted Messages**

When message includes `__session_id`, deliver only to that session:

```javascript
{
    "type": "gui.page.show",
    "data": {
        "page_names": ["weather"],
        "__from": "weather_skill",
        "__session_id": "living_room_tablet"  // ← Only this session receives
    }
}
```

**Rule 2: Site-Targeted Messages (Site-ID Sync Mode)**

When site-ID sync mode is enabled and message includes `__site_id`, deliver to all sessions at that site:

```javascript
{
    "type": "gui.page.show",
    "data": {
        "page_names": ["music"],
        "__from": "music_skill",
        "__site_id": "kitchen"  // ← All GUIs with site_id="kitchen" receive
    }
}
```

**Rule 3: Default Routing (Backward Compatible)**

If neither `__session_id` nor `__site_id` is specified, default to `session_id="default"`:

```javascript
{
    "type": "gui.page.show",
    "data": {
        "page_names": ["weather"],
        "__from": "weather_skill"
        // No __session_id or __site_id → routes to session="default"
    }
}
```

## Message Filtering

GUI clients **must filter incoming messages** to only process those intended for their session:

**Pseudocode:**
```
On message received:
  if message has __session_id:
    if this_client.session_id != message.__session_id:
      ignore message  // Not for this session
  else if message has __site_id:
    if site_id_sync_enabled and this_client.site_id != message.__site_id:
      ignore message  // Not for this site
  // Process message
```

---

# Multi-Session Examples

## Example 1: On-Device Only (Default Behavior)

```javascript
// Skill sends normal message (no session info)
{
    "type": "gui.page.show",
    "data": {
        "page_names": ["weather"],
        "__from": "weather_skill"
    }
}

// ovos-gui routes to: session_id="default"
// Clients with session_id="default" → show weather
// All other clients → ignore message
```

## Example 2: Remote GUI Gets Dedicated Update

```javascript
// Desktop app skill targets specific session
{
    "type": "gui.page.show",
    "data": {
        "page_names": ["launcher"],
        "__from": "app_launcher",
        "__session_id": "desktop_app"
    }
}

// ovos-gui routes to: session_id="desktop_app"
// Clients with session_id="desktop_app" → show launcher
// All other clients (including on-device) → ignore
```

## Example 3: Multi-Location (Site-ID Sync Mode)

```javascript
// Message targets entire kitchen (site_id_sync_mode=true)
{
    "type": "gui.page.show",
    "data": {
        "page_names": ["music"],
        "__from": "music_skill",
        "__site_id": "kitchen"
    }
}

// ovos-gui routes to: all sessions with site_id="kitchen"
// Clients with site_id="kitchen" → all show music identically
// Clients at other sites → ignore message
```

---

# NAMESPACES

ovos-gui maintains a list of namespaces with GUI data, namespaces usually correspond to a skill_id

Every message in the gui protocol specifies a namespace it belongs to

gui clients usualy display all namespaces, but can be requested to display a single one, 

eg, have a dedicated window to show a skill as a [traditional desktop app](https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/blob/dev/ovos_plugin_common_play/ocp/res/desktop/OCP.desktop)


## Active Skills - mycroft.system.active_skills

a reserved namespace is "mycroft.system.active_skills", the data contained in this namespace defines the namespace display priority

Recent skills are ordered from the last used to the oldest, so the first item of the list will always be the the one showing any GUI page, if available.

see the section about [lists](https://github.com/OpenVoiceOS/ovos-gui/blob/dev/protocol.md#lists) if you need to modify active skills


# PAGES - mycroft.gui.list.xxx

Each active skill is associated with a list of uris to the QML files of all gui items that are supposed to be visible.

Non QT GUIS get sent other file extensions such as .jsx or .html using the same message format

If a gui resource can not be resolved to a url (*url* may be `None`!), it might still exist client side, it is the clients responsibility to handle the namespace/page in that case

> eg, a client could map namespaces/page to a remote http server url 

## Insert new page at position
```javascript
{
    "type": "mycroft.gui.list.insert",
    "namespace": "mycroft.weather"
    "position": 2
    "values": [{"url": "file://..../currentWeather.qml", "page": "currentWeather"}, ...] //values must always be in array form
}
```

## Move pages within the list
```javascript
{
    "type": "mycroft.gui.list.move",
    "namespace": "mycroft.weather"
    "from": 2
    "to": 5
    "items_number": 2 //optional in case we want to move a big chunk of list at once
}
```

## Remove pages from the list
```javascript
{
    "type": "mycroft.gui.list.remove",
    "namespace": "mycroft.weather"
    "position": 2
    "items_number": 5 //optional in case we want to get rid a big chunk of list at once
}
```


# EVENTS - mycroft.events.triggered

Events can either be emitted by a gui client (eg, some element clicked) or by the skill (eg, in response to a voice command)

```javascript
{
    "type": "mycroft.events.triggered"
    "namespace": "my_skill_id"
    "event_name": "my.gui.event",
    "parameters": {"item": 3}
}
```

## SPECIAL EVENT: page_gained_focus

This event is used when the ovos-gui wants a page of a particular skill to gain user attention focus and become the current active view and "focus of attention" of the user. 

when a GUI client receives it, it should render the requested GUI page

GUI clients can also emit this event, if a new page was rendered (eg, in response to a user swipping left)

NOTE: for responsiveness it is recommened this message is only emitted after the rendering has actually been done, skills may be waiting for this event to initiate some actons

```javascript
{
    "type": "mycroft.events.triggered",
    "namespace": "mycroft.weather",
    "event_name": "page_gained_focus",
    "data": {"number": 0}
}
```

The parameter "number" is the position (starting from zero) of the page

# SKILL DATA - mycroft.session.xxx

At the center of data sharing there is a key/value dictionary that is kept synchronized between ovos-gui and the GUI client.

Values can either be simple strings, numbers and booleans or be more complicated data types

this event can be sent from gui clients (eg, in response to a dropdown selection) or from skills (eg, change weather data)

NOTE: Once a new gui client connects to ovos-gui, all existing session data is sent to the client, 
after that the client gets live updates via these events

## Sets a new key/value in the sessionData dictionary

Either sets a new key/value pair or replace an existing old value.

```javascript
{
    "type": "mycroft.session.set",
    "namespace": "weather.mycroft"
    "data": {
        "temperature": "28",
        "icon": "cloudy",
        "forecast": [{...},...] //if it's a list see below for more message types
    }
}
```

## Deletes a key/value pair from the sessionData dictionary
```javascript
{
    "type": "mycroft.session.delete",
    "namespace": "weather.mycroft"
    "property": "temperature"
}
```

## Lists

### Inserts new items at position
```javascript
{
    "type": "mycroft.session.list.insert",
    "namespace": "weather.mycroft"
    "property": "forecast" //the key of the main data map this list in contained into
    "position": 2
    "values": [{"date": "tomorrow", "temperature" : 13, ...}, ...] //values must always be in array form
}
```

### Updates item values starting at the given position, as many items as there are in the array
```javascript
{
    "type": "mycroft.session.list.update",
    "namespace": "weather.mycroft"
    "property": "forecast"
    "position": 2
    "values": [{"date": "tomorrow", "temperature" : 13, ...}, ...] //values must always be in array form
}
```

### Move items within the list
```javascript
{
    "type": "mycroft.session.list.move",
    "namespace": "weather.mycroft"
    "property": "forecast"
    "from": 2
    "to": 5
    "items_number": 2 //optional in case we want to move a big chunk of list at once
}
```

### Remove items from the list
```javascript
{
    "type": "mycroft.session.list.remove",
    "namespace": "weather.mycroft"
    "property": "forecast"
    "position": 2
    "items_number": 5 //optional in case we want to get rid a big chunk of list at once
}
```

---

# SHELL FEATURES OVERVIEW

## Client Connection Architecture

**CRITICAL**: Qt GUI clients connect **ONLY** to port 18181/gui WebSocket. The OVOS MessageBus (port 8181) is **internal only**.

| Component | Port | Route | Access | Purpose |
|-----------|------|-------|--------|---------|
| **OVOS Core MessageBus** | 8181 | `/core` | **INTERNAL ONLY** | System events (skills, recognition, TTS) |
| **GUI WebSocket** | 18181 | `/gui` | **Qt clients** | Templates + shell features |

Shell feature messages are standardized extensions to the core protocol, prefixed with `gui.*`, enabling bidirectional communication for system-wide settings (brightness, color schemes, notifications, widgets, configuration).

---

# BRIGHTNESS CONTROL

## gui.brightness.set

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
- Emit `ovos.shell.brightness.set` to OVOS services

---

## gui.brightness.get

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

## gui.brightness.auto_dim.set

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
- Emit `ovos.shell.brightness.auto_dim.set` bus message

---

## gui.brightness.night_mode.set

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
- Emit `ovos.shell.brightness.night_mode.set` bus message

---

# COLOR SCHEME MANAGEMENT

## gui.color_scheme.set

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
- Emit `ovos.shell.color_scheme.generated` bus message

---

## gui.color_scheme.get

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

# NOTIFICATIONS

## gui.notification.set

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

## gui.notification.clear

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
- Emit `ovos.shell.notification.clear` bus message

---

# WIDGETS

## gui.widget.display

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

## gui.widget.remove

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

# CONFIGURATION UI

## gui.config.list.get

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

## gui.config.get

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

## gui.config.set

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
- Emit `ovos.shell.configuration.set` bus message

---

## Message Type Reference

| Message Type | Direction | Purpose |
|---|---|---|
| `gui.brightness.set` | C→S | Set brightness level |
| `gui.brightness.get` | C→S | Get current brightness |
| `gui.brightness.get.response` | S→C | Response with brightness |
| `gui.brightness.auto_dim.set` | C→S | Toggle auto-dim |
| `gui.brightness.night_mode.set` | C→S | Toggle night mode |
| `gui.color_scheme.set` | C↔S | Save color theme |
| `gui.color_scheme.get` | C→S | Get active theme |
| `gui.color_scheme.get.response` | S→C | Response with theme |
| `gui.notification.set` | S→C | Display notification |
| `gui.notification.clear` | C→S | Dismiss notification |
| `gui.widget.display` | S→C | Display widget |
| `gui.widget.remove` | C↔S | Remove widget |
| `gui.config.list.get` | C→S | Get config groups |
| `gui.config.list.get.response` | S→C | Response with groups |
| `gui.config.get` | C→S | Get group config |
| `gui.config.get.response` | S→C | Response with config |
| `gui.config.set` | C→S | Save config changes |


