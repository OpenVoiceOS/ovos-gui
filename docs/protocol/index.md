# GUI Protocol Documentation

**Clarification**: OVOS GUI has multiple layers of protocol, depending on context and audience.

---

## 1. **Qt GUI WebSocket Protocol** (Client-Specific)

**Audience**: Qt adapter developers, Qt client developers (mycroft-gui-qt5, mycroft-gui-qt6)

**File**: [qt-gui-protocol.md](qt-gui-protocol.md)

This is the **WebSocket wire format** for Qt GUI clients communicating with ovos-gui service.

- Connection handshake (gui_id, session_id, site_id)
- Namespace/skill activation
- Page list management
- Event handling (page_gained_focus, page interactions)
- Session data updates (SKILL DATA)
- Shell feature extensions (brightness, color scheme, notifications, widgets, config)

**Protocol Details**:
- Transport: WebSocket (port 18181 default)
- Message format: JSON serialized
- Session routing: `__session_id`, `__site_id` parameters

**Backward Compatibility**: Full backward compatibility with legacy Mycroft AI protocol.

---

## 2. **MessageBus Protocol** (Generic to All Adapters)

**Audience**: Skill developers, adapter developers (all GUI client types)

**File**: [../adapter-development/bus-protocol.md](../adapter-development/bus-protocol.md)

This is the **skill-to-GUI message format** that flows over the OVOS MessageBus.

- `gui.page.show` — Show skill content (template-based)
- `gui.value.set` — Update session data
- `gui.page.delete` — Remove pages from namespace
- `gui.clear.namespace` — Hide skill content
- System events (wakeword, sleep, etc.)

**Key Points**:
- Works with ANY GUI adapter (Qt, web, terminal, accessibility, etc.)
- NamespaceManager routes these to all loaded adapters
- Each adapter renders according to its own protocol (Qt uses WebSocket, web uses HTTP, etc.)

---

## 3. **Routing & Session Management** (All Contexts)

**Audience**: System integrators, adapter developers

**Files**:
- [ROUTING_KEY_GUIDE.md](../ROUTING_KEY_GUIDE.md) — How session_id/site_id routing works
- [SESSION_AND_SITE_ID_DESIGN.md](../SESSION_AND_SITE_ID_DESIGN.md) — Multi-session architecture

This describes how ovos-gui isolates state and routes messages to clients in single-screen, multi-room, and remote client scenarios.

---

## Protocol Flow Diagram

```
Skill (Python)
    ↓ (OVOS MessageBus)
[gui.page.show, gui.value.set, etc.]
    ↓
NamespaceManager (ovos-gui)
    ↓ (Adapter Callbacks)
[on_namespace_activated(), on_session_update(), etc.]
    ↓
GUI Adapters (Plugins)
    ├→ Legacy Qt Adapter
    │   ↓ (WebSocket - QtGUI Protocol)
    │   → mycroft-gui-qt5 / qt6 client
    │
    ├→ PyHTMX Web Adapter
    │   ↓ (HTTP/REST API)
    │   → Web browser clients
    │
    └→ Other Adapters (Terminal, Accessibility, etc.)
        ↓ (Custom protocols)
        → Various clients
```

---

## Key Distinction

**MessageBus Protocol** (skill → ovos-gui):
- Generic, used by ALL skills
- Works with ANY adapter
- What skills use to display content

**Qt GUI Protocol** (Qt client ↔ ovos-gui):
- Qt-specific
- ONLY for legacy Qt clients
- How Qt clients render content
- Not relevant to web, terminal, or accessibility adapters

---

## Selection Guide

**I'm building a Qt client** (or modifying mycroft-gui-qt5/qt6)
→ Read [qt-gui-protocol.md](qt-gui-protocol.md)

**I'm building a skill** or **custom GUI adapter** (web, terminal, accessibility)
→ Read [MessageBus Protocol](../adapter-development/bus-protocol.md)

**I'm integrating multi-room deployment** or **custom routing**
→ Read [ROUTING_KEY_GUIDE.md](../ROUTING_KEY_GUIDE.md)

---

**Last Updated**: 2026-03-12

**Status**: Formal separation of concerns. Protocol documentation is now organized by audience and context.
