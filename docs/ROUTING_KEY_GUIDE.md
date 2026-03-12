# GUI Routing Key: Adapter Targeting Guide

**TECH-007 Documentation**: Clarifying `site_id` semantics in multi-device scenarios

## Overview

When ovos-gui notifies adapters of state changes, it passes a `site_id` parameter. This parameter serves as the **routing key** for adapter client targeting in multi-device and multi-room scenarios.

## Routing Key Semantics

The routing key is computed using `NamespaceManager._gui_routing_key()` which applies priority logic:

```
routing_key = _get_session_key(session_id, site_id)

Where _get_session_key():
  1. If site_id is meaningful (not "unknown") → return site_id
  2. Otherwise → return session_id
```

## Practical Examples

### Single-Screen Deployment (Default)

```
session_id = "default"
site_id = "unknown"     (or missing)
routing_key = "default" (session_id wins)

→ Adapter targets: The single local display
```

### Multi-Room Deployment (Site-Based Routing)

```
Three Mark2 devices in the kitchen:

Device 1: session_id = "mark2-kitchen-1",  site_id = "kitchen"  → routing_key = "kitchen"
Device 2: session_id = "mark2-kitchen-2",  site_id = "kitchen"  → routing_key = "kitchen"
Device 3: session_id = "mark2-kitchen-3",  site_id = "kitchen"  → routing_key = "kitchen"

All three devices in the same site receive the same GUI state.

→ Adapter targets: All clients registered for site_id="kitchen"
```

### Remote Client (UUID-Based Routing)

```
session_id = "abc123-def456-ghi789"  (unique client UUID)
site_id = "unknown"
routing_key = "abc123-def456-ghi789" (session_id wins)

→ Adapter targets: The specific remote client with that UUID
```

## Adapter Callback Signatures

When ovos-gui notifies adapters, it passes `site_id` as the routing key:

```python
# Namespace activation (skill display)
adapter.on_namespace_activated(
    namespace_name: str,      # e.g., "weather.skill"
    session_id: str,          # e.g., "default" or UUID
    site_id: str              # Routing key for client targeting
)

# Namespace deactivation (hide skill)
adapter.on_namespace_deactivated(
    namespace_name: str,
    session_id: str,
    site_id: str              # Routing key
)

# Data update (gui[key] = value)
adapter.on_session_update(
    namespace_name: str,
    data: dict,               # Updated session data
    session_id: str,
    site_id: str              # Routing key
)

# System event (wakeword, sleep, etc.)
adapter.on_status_event(
    msg_type: str,            # e.g., "recognizer_loop:wakeword"
    data: dict,
    site_id: str              # Routing key
)
```

## Adapter Implementation Guidance

### Using `site_id` for Client Targeting

**When** `site_id` is meaningful (not "unknown"):
- It identifies a location/site group (e.g., "kitchen", "bedroom")
- Use it to route the GUI state to all clients at that site
- Example: Multi-room mark2 setup where all kitchen devices show the same display

**When** `site_id` is "unknown":
- Fall back to `session_id` as the routing key
- Use `session_id` to target a specific client/session
- Example: Single-screen device or remote client with unique UUID

### Example Adapter Implementation

```python
class MyGUIAdapter(AbstractGUIPlugin):
    def on_namespace_activated(self, namespace_name, session_id, site_id):
        """Show a skill on the GUI."""
        # Determine routing target
        routing_key = site_id if site_id != "unknown" else session_id

        # Send to appropriate client(s)
        self.send_to_clients(routing_key, {
            "action": "show",
            "skill": namespace_name
        })

    def on_session_update(self, namespace_name, data, session_id, site_id):
        """Update skill data on the GUI."""
        routing_key = site_id if site_id != "unknown" else session_id

        self.send_to_clients(routing_key, {
            "action": "update_data",
            "skill": namespace_name,
            "data": data
        })
```

## State Isolation Across Sites

ovos-gui maintains separate `GUISession` objects for each site/routing key. This ensures:

1. **Visual isolation**: Kitchen display shows only kitchen-relevant content
2. **Data isolation**: Bedroom namespace data doesn't leak to kitchen display
3. **Independent stacks**: Each site has its own LIFO namespace stack

## Related Documentation

- `ovos_gui/namespace.py:_get_session_key()` - Routing key computation
- `ovos_gui/namespace.py:_gui_routing_key()` - Message-based routing key extraction
- `ovos_gui/namespace.py:_get_routing_info()` - Extract session_id and site_id from message
- `docs/adapter-development/adapter-plugins.md` - Full adapter interface documentation

## Questions?

See `docs/FAQ.md` → "How do I target different displays?" or "What's the difference between session_id and site_id?"
