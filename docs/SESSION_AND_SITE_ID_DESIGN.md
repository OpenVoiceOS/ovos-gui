# Session and Site-ID Design — OVOS GUI Architecture

**Comprehensive guide to multi-screen and multi-device GUI state management in OVOS.**

---

## Overview

OVOS GUI supports **multi-device and multi-screen scenarios** through two complementary concepts:

- **`session_id`** — Unique identifier for a GUI client instance or logical screen
- **`site_id`** — Unique identifier for a physical location/installation, grouping multiple screens

This document explains how these identifiers partition GUI state, enable multi-device deployments, and maintain data isolation across different screens and sites.

---

## Core Concepts

### Session ID

A **session** represents a single GUI client or screen that receives its own isolated GUI state.

| Scenario | session_id | Description |
|----------|-----------|-------------|
| **On-Device (Single Screen)** | `"default"` | Standard OVOS device with built-in or single connected screen |
| **Remote GUI Client** | Custom (e.g., `"living_room_tablet"`) | External device connecting to ovos-gui service |
| **Satellite + On-Device** | Same value | Both report identical session_id, so state is **shared** |
| **Multi-Screen Same Location** | Different values | Each screen gets isolated state |

**Key Rule:** Each unique `session_id` receives its own copy of:
- Active namespace stack (`active_namespaces`)
- Loaded namespaces (`loaded_namespaces`)
- Session data (`sessionData`)
- Page list and focus state

### Site ID

A **site** is a physical location containing one or more screens. The `site_id` enables **multi-location deployments** where devices at the same location share GUI state.

| Scenario | site_id | Behavior |
|----------|---------|----------|
| **Single Location** | `"default"` | One site, can have multiple session_ids |
| **Multi-Location** | Unique per location (e.g., `"kitchen"`, `"bedroom"`) | State shared across all GUI clients **at that site** |
| **Same Site, Different Session** | Same site_id, different session_id | Both sessions receive **identical state updates** |

**Site-ID Sync Mode (Optional):** When enabled, ovos-gui treats all `session_id` values belonging to the same `site_id` as a single virtual session. Any state change overwrites state for all clients at that site.

---

## Message Routing and Filtering

### Rule 1: Session-Based Message Delivery

GUI clients **only receive messages for their own `session_id`**.

```
Core Bus (ovos-core) sends:
  {
    "type": "gui.page.show",
    "data": {
      "page_names": [...],
      "__from": "skill_id",
      "__session_id": "living_room_tablet"  // ← target session
    }
  }
         ↓
ovos-gui receives message
         ↓
Only GUI client with session_id="living_room_tablet" receives the message
All other connected GUIs see nothing
```

### Rule 2: Site-ID Grouping (Optional)

When **site_id sync mode** is enabled:
- Messages target `site_id`, not `session_id`
- All GUIs reporting the same `site_id` receive identical state updates

```
ovos-gui (site_id sync mode):
  {
    "type": "gui.page.show",
    "data": {
      "page_names": [...],
      "__from": "skill_id",
      "__site_id": "kitchen"  // ← target site
    }
  }
         ↓
All GUI clients with site_id="kitchen" receive update
All other sites see nothing
```

### Rule 3: Default Behavior (No Session/Site Specified)

If neither `__session_id` nor `__site_id` is present in a message:
- Default to `session_id="default"` (on-device screen)
- Ensures backward compatibility with legacy skills

---

## Architecture: How ovos-gui Organizes State

ovos-gui maintains state using **sessions as the primary organizational unit**:

```python
class GUISession:
    """Represents a single GUI screen or client."""
    session_id: str
    loaded_namespaces: Dict[str, Namespace]  # Per-session namespace cache
    active_namespaces: List[Namespace]       # Per-session active stack (LIFO)
    remove_namespace_timers: Dict[str, Timer] # Per-session cleanup timers

class NamespaceManager:
    """Manages all sessions and routes messages."""
    sessions: Dict[session_id, GUISession]  # All connected sessions

    def get_session(session_id: str) -> GUISession:
        """Retrieve or create a session."""
```

When a message arrives with `__session_id` or `__site_id`:

1. **Compute routing key** — use `__session_id` directly, or compute session(s) from `__site_id`
2. **Retrieve target session** — get `GUISession` object from `sessions` dict
3. **Modify target session state** — update namespace stack, pages, data
4. **Notify adapters for target session** — call adapter callbacks with routing key

```
Message arrives:
  {
    "type": "gui.page.show",
    "__from": "skill_id",
    "__session_id": "living_room_tablet"
  }
       ↓
ovos-gui:
  session = manager.get_session("living_room_tablet")
  session.active_namespaces.add(namespace)
  adapters.on_namespace_activated(namespace, session_id="living_room_tablet")
       ↓
Only adapters linked to "living_room_tablet" render the page
```

---

## Implementation Details

### Session Initialization

Clients announce themselves on connection:

```javascript
// GUI client connects to WebSocket port 18181
{
  "type": "mycroft.gui.connected",
  "gui_id": "unique_id",
  "session_id": "living_room_tablet",   // ← custom session ID
  "site_id": "kitchen"                  // ← optional, for multi-location
}
```

**Backward Compatibility:** If `session_id` is omitted, default to `"default"`.

### State Partitioning

Each session maintains **completely isolated state**:

```
Session "default" (on-device):
  active_namespaces = [weather, music]
  sessionData = {"temp": 22, "artist": "Bach"}

Session "tablet" (living room tablet):
  active_namespaces = [news, stocks]
  sessionData = {"headlines": [...], "AAPL": 150}

→ User asks: "What's the temperature?"
  Message target: session_id="default"
  → Only on-device screen shows weather, temperature=22
  → Tablet continues showing stocks
```

### Site-ID Sync Mode

When enabled, ovos-gui automatically computes which sessions belong to a site:

```python
# In NamespaceManager.__init__:
site_id_sync_mode = config.get("gui.site_id_sync_mode", False)

# When processing message with __site_id:
if site_id_sync_mode and "__site_id" in message.data:
    site_id = message.data["__site_id"]
    target_sessions = [
        s for s in sessions.values()
        if s.site_id == site_id
    ]
    # Update all sessions at that site identically
```

---

## Multi-Device Scenarios

### Scenario 1: On-Device + Satellite

Both report same `session_id="default"` → **shared state**

```
OVOS Core Device (on-device screen):
  session_id = "default"
  Connected adapters: qt_gui (local)

Satellite Device (running ovos-gui client):
  session_id = "default"
  Connected adapters: none (listening only)

Skill plays music:
  Message: {"type": "gui.page.show", "__from": "music_skill"}
  → Routes to session "default"
  → Both on-device AND satellite see same GUI state
```

### Scenario 2: Remote GUI for Same Device

Desktop app connecting to same ovos-gui instance:

```
OVOS Core Device:
  ovos-gui service running (1 instance)

On-Device Screen:
  session_id = "default"
  Sees: weather, music

Desktop App (same device):
  session_id = "desktop_app"
  Sees: separate state (e.g., app launcher, system status)

Each maintains independent state through different session_id
```

### Scenario 3: Multi-Location with Site-ID Sync

Multiple locations, each with multiple screens:

```
Kitchen (site_id="kitchen"):
  GUI1: session_id="kitchen_screen1" → site_id="kitchen"
  GUI2: session_id="kitchen_tablet"  → site_id="kitchen"

  With site_id_sync=true:
    Any message to site_id="kitchen" updates BOTH screens identically

Bedroom (site_id="bedroom"):
  GUI1: session_id="bedroom_screen"  → site_id="bedroom"

  Message targets site_id="bedroom":
    Only bedroom screen updates, kitchen unchanged
```

---

## Protocol Extensions

### Connection Message

```javascript
{
  "type": "mycroft.gui.connected",
  "gui_id": "unique_client_identifier",
  "session_id": "living_room_tablet",  // Optional, defaults to "default"
  "site_id": "kitchen"                  // Optional, for site-ID grouping
}
```

**Fields:**
- `gui_id` — Unique identifier for this client (used for reconnection, debugging)
- `session_id` — Session identifier (if omitted, uses `"default"`)
- `site_id` — Site identifier for multi-location deployments (optional)

### Message Routing Fields

All messages from core bus should include:

```javascript
{
  "type": "gui.page.show",
  "data": {
    "page_names": [...],
    "__from": "skill_id",
    "__session_id": "specific_session",  // Send to this session only
    // OR
    "__site_id": "kitchen",              // Send to all sessions at this site
    "__idle": 10                         // Auto-remove after 10 seconds
  }
}
```

**Routing Priority:**
1. If `__session_id` present → route to that specific session
2. Else if `__site_id` present → route to all sessions at that site (if sync mode enabled)
3. Else → route to `session_id="default"` (backward compatible)

---

## Qt GUI Client Implementation

### Launch Parameters

Both mycroft-gui-qt5 and mycroft-gui-qt6 should accept launch kwargs:

```bash
# Default (on-device)
mycroft-gui-qt6

# Custom session (desktop app)
mycroft-gui-qt6 --session-id="desktop_app" --site-id="default"

# Remote GUI (tablet in living room)
mycroft-gui-qt6 --session-id="living_room_tablet" --site-id="kitchen"

# Via Python
from mycroft_gui import MycroftGUI
gui = MycroftGUI(
    session_id="living_room_tablet",
    site_id="kitchen"
)
gui.run()
```

### Connection Handshake

Qt client must send connection message with session info:

```cpp
// In WebSocketClient::onConnected()
QJsonObject message;
message["type"] = "mycroft.gui.connected";
message["gui_id"] = generate_unique_id();
message["session_id"] = session_id;  // From launch param or config
message["site_id"] = site_id;        // From launch param or config

emit_to_server(message);
```

### Message Filtering

Qt client should **ignore all messages not intended for its session**:

```cpp
void MycroftGUI::on_message_received(const QJsonObject& msg) {
    // Extract target session from message
    QString target_session = msg["data"]["__session_id"].toString("default");
    QString target_site = msg["data"]["__site_id"].toString("");

    // Check if message is for this client
    if (!target_site.isEmpty()) {
        // Site-targeted message
        if (config.site_id_sync_mode && this->site_id != target_site) {
            return;  // Ignore, not for our site
        }
    } else {
        // Session-targeted message
        if (this->session_id != target_session) {
            return;  // Ignore, not for our session
        }
    }

    // Process message
    handle_message(msg);
}
```

---

## Configuration

### ovos-gui Service

```yaml
# mycroft.conf
gui:
  # Enable site-ID sync mode (optional)
  # When true, all sessions with same site_id share state
  site_id_sync_mode: false

  # Default session/site for backward compatibility
  default_session_id: "default"
  default_site_id: "default"
```

### Qt GUI Client

```yaml
# mycroft.conf or environment
gui:
  # Session identifier for this client
  session_id: "default"

  # Site identifier (for multi-location deployments)
  site_id: "default"
```

---

## Message Examples

### Example 1: On-Device Skill Show Page

```javascript
// Skill sends to core bus (normal scenario, no session specified)
{
  "type": "gui.page.show",
  "data": {
    "page_names": ["weather_page"],
    "__from": "mycroft.weather"
  }
}

// ovos-gui:
//   1. No __session_id, no __site_id → default to "default"
//   2. Update session["default"].active_namespaces
//   3. Call adapters.on_namespace_activated(..., session_id="default")
//   4. On-device screen shows weather

// Result: Only the on-device screen (session="default") shows weather
```

### Example 2: Remote GUI Gets Exclusive Update

```javascript
// Desktop app skill sends with explicit session
{
  "type": "gui.page.show",
  "data": {
    "page_names": ["launcher"],
    "__from": "app_launcher",
    "__session_id": "desktop_app"
  }
}

// ovos-gui:
//   1. Route to session["desktop_app"]
//   2. Call adapters.on_namespace_activated(..., session_id="desktop_app")

// Result: Only the desktop app GUI shows launcher, on-device screen unaffected
```

### Example 3: Site-ID Sync (Multi-Location)

```javascript
// With site_id_sync_mode=true
{
  "type": "gui.page.show",
  "data": {
    "page_names": ["music"],
    "__from": "music_skill",
    "__site_id": "kitchen"
  }
}

// ovos-gui:
//   1. Find all sessions where site_id="kitchen"
//   2. Update each: session[s].active_namespaces
//   3. Call adapters for each session
//      on_namespace_activated(..., session_id="kitchen_screen1")
//      on_namespace_activated(..., session_id="kitchen_tablet")

// Result: Both kitchen screens show music identically
```

---

## Backward Compatibility

**No changes required for legacy skills.** If a skill doesn't specify `__session_id` or `__site_id`:

1. ovos-gui defaults to `session_id="default"`
2. On-device screen (session="default") receives the message
3. All other sessions are unaffected

This ensures:
- Existing OVOS installations continue working
- New multi-session deployments opt-in via explicit routing
- Skills need not be aware of multi-session complexity

---

## Implementation Checklist

### ovos-gui

- [ ] Refactor `NamespaceManager` to organize state by `session_id`
- [ ] Implement `GUISession` class for per-session state
- [ ] Add message routing logic (extract `__session_id` or `__site_id`)
- [ ] Add configuration option for `site_id_sync_mode`
- [ ] Update adapter callback signatures to include `session_id`
- [ ] Document in this file + protocol.md

### mycroft-gui-qt5

- [ ] Accept `--session-id` and `--site-id` command-line args
- [ ] Send connection message with session/site info
- [ ] Filter incoming messages by session (ignore messages for other sessions)
- [ ] Document launch parameters + configuration

### mycroft-gui-qt6

- [ ] Accept `--session-id` and `--site-id` command-line args
- [ ] Send connection message with session/site info
- [ ] Filter incoming messages by session
- [ ] Document launch parameters + configuration

---

## See Also

- `protocol.md` — Complete wire protocol specification
- `adapter-development/architecture.md` — Adapter integration patterns
- `QUICK_FACTS.md` — Package info and entry points

