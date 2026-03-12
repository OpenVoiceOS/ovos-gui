# MessageBus Protocol

This document lists every bus message the OVOS GUI layer produces or consumes.

---

## Messages emitted by skills (via `GUIInterface`)

### `gui.value.set`

Sent by `GUIInterface.__setitem__` / `_sync_data()` to write session variables into the skill's namespace.

```json
{
  "type": "gui.value.set",
  "data": {
    "current_temp": 22,
    "condition": "Sunny",
    "__from": "ovos-skill-weather",
    "__idle": null,
    "__animations": false
  }
}
```

| Field | Description |
|---|---|
| `__from` | Skill ID (namespace owner) |
| `__idle` | Idle timeout in seconds, or `null` |
| `__animations` | Whether page transitions should animate |
| All other keys | Skill-defined session variables |

`NamespaceManager` stores all keys in `namespace.data` and forwards non-reserved keys to adapters via `on_session_update()`.

---

### `gui.page.show`

Sent by `GUIInterface._show_pages()` to request a template or page be shown.

**New format (template-based):**

```json
{
  "type": "gui.page.show",
  "data": {
    "page_names": ["SYSTEM_weather"],
    "index": 0,
    "persistence": true,
    "__from": "ovos-skill-weather",
    "__idle": null,
    "__animations": false
  }
}
```

When `page_names[0]` starts with `SYSTEM_`, `NamespaceManager` reads the namespace's current `data` dict and dispatches to all loaded adapters via `adapter.dispatch_template(template, skill_id, data)`.

**Legacy format (framework-specific pages):**

```json
{
  "type": "gui.page.show",
  "data": {
    "page_names": ["Weather.qml"],
    "index": 0,
    "__from": "ovos-skill-weather"
  }
}
```

Non-SYSTEM_* names are handled by the unchanged legacy path inside `NamespaceManager` (forwarded to Qt clients via the legacy adapter).

---

### `gui.page.delete`

Removes a specific page from a skill's namespace page list.

```json
{
  "type": "gui.page.delete",
  "data": {
    "page_names": ["Weather.qml"],
    "__from": "ovos-skill-weather"
  }
}
```

---

### `gui.page.delete.all`

Clears all pages from a skill's namespace.

```json
{
  "type": "gui.page.delete.all",
  "data": {
    "__from": "ovos-skill-weather"
  }
}
```

---

### `gui.event.send`

Sends an arbitrary event into a skill's namespace (used for confirm/select responses, custom interactions).

```json
{
  "type": "gui.event.send",
  "data": {
    "namespace": "ovos-skill-weather",
    "event_name": "skill.selection.confirmed",
    "params": {"confirmed": true}
  }
}
```

---

## Messages consumed by `NamespaceManager` (from skills / core)

### `ovos.gui.screen.close`

Request to remove a skill's namespace from the active display stack and deactivate it.

```json
{
  "type": "ovos.gui.screen.close",
  "data": {
    "skill_id": "ovos-skill-weather"
  }
}
```

Triggers `adapter.on_namespace_deactivated(skill_id)` on all adapters.

---

### `gui.clear.namespace`

Legacy equivalent of `ovos.gui.screen.close`. Cleared namespace is deactivated and session data is discarded.

```json
{
  "type": "gui.clear.namespace",
  "data": {
    "__from": "ovos-skill-weather"
  }
}
```

---

## Status events forwarded to adapters

`NamespaceManager` subscribes to the following core bus messages and forwards them to all adapters via `adapter.on_status_event(event_name, data)`:

| Bus message type | `event_name` passed to adapters |
|---|---|
| `recognizer_loop:wakeword` | `recognizer_loop:wakeword` |
| `recognizer_loop:record_begin` | `recognizer_loop:record_begin` |
| `recognizer_loop:record_end` | `recognizer_loop:record_end` |
| `recognizer_loop:utterance` | `recognizer_loop:utterance` |
| `recognizer_loop:recognition_unknown` | `recognizer_loop:recognition_unknown` |
| `speak` | `speak` |
| `recognizer_loop:audio_output_start` | `recognizer_loop:audio_output_start` |
| `recognizer_loop:audio_output_end` | `recognizer_loop:audio_output_end` |
| `recognizer_loop:sleep` | `recognizer_loop:sleep` |
| `recognizer_loop:wake_up` | `recognizer_loop:wake_up` |
| `mycroft.awoken` | `mycroft.awoken` |
| `ovos.utterance.handled` | `ovos.utterance.handled` |
| `ovos.utterance.cancelled` | `ovos.utterance.cancelled` |

---

## Messages emitted by `ovos-gui` service

### `gui.namespace.removed`

Emitted by `NamespaceManager` after a namespace has been deactivated and cleared.

```json
{
  "type": "gui.namespace.removed",
  "data": {
    "skill_id": "ovos-skill-weather"
  }
}
```

---

### `gui.namespace.displayed`

Emitted when a namespace moves to the top of the active display stack.

```json
{
  "type": "gui.namespace.displayed",
  "data": {
    "skill_id": "ovos-skill-weather"
  }
}
```

---

## Qt client negotiation (via `ovos-legacy-mycroft-gui-plugin`)

These messages are only active when the legacy adapter is installed.

### `mycroft.gui.connected` (consumed)

Sent by a Qt GUI client after it establishes a connection. The legacy adapter replies with the WebSocket port.

```json
{
  "type": "mycroft.gui.connected",
  "data": {
    "gui_id": "qt-client-1",
    "framework": "qt5"
  }
}
```

### `mycroft.gui.port` (emitted by legacy adapter)

Reply to `mycroft.gui.connected`.

```json
{
  "type": "mycroft.gui.port",
  "data": {
    "port": 18181,
    "gui_id": "qt-client-1",
    "framework": "qt5"
  }
}
```

See [legacy-qt-plugin.md](legacy-qt-plugin.md) for the full Qt WebSocket protocol.

---

## Touch / interaction responses (emitted by adapters back to the bus)

When a touch-capable adapter receives user input on confirm/select templates:

### `<skill_id>.confirm.response`

```json
{
  "type": "ovos-skill-weather.confirm.response",
  "data": {
    "confirmed": true
  }
}
```

### `<skill_id>.select.response`

```json
{
  "type": "ovos-skill-weather.select.response",
  "data": {
    "value": "Berlin"
  }
}
```

Skills must register handlers for these events if they use `show_confirm()` or `show_select()`.
