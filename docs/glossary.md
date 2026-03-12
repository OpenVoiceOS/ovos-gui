# Glossary — OVOS GUI Terminology

Quick reference for terms used in the OVOS GUI system.

## A

**Adapter** — A GUI rendering plugin that displays templates on a specific platform (Qt5, web, terminal, etc.). Implements `AbstractGUIPlugin` and registers via `opm.gui_adapter` entry point.

**Application ID** — See [Skill ID](#skill-id).

## B

**Bus** — See [MessageBus](#messagebus).

## C

**Context** — Metadata attached to a message (origin, timestamp, target). Also used for "session context" — temporary state shared between skill and adapter.

**CRUD** — Create, Read, Update, Delete operations. Not directly relevant to GUI, but used in tests.

## D

**Data Template** — See [Template](#template).

**Decorator** — Python function wrapper that modifies behavior. OVOS uses decorators like `@intent_handler` to register skill methods.

## E

**Event** — A message emitted on the MessageBus. Examples: `gui.request_page`, `gui.user_input`, `gui.session_update`.

**Event Handler** — A skill method that listens for and responds to a specific event.

## F

**FakeBus** — An in-memory MessageBus replacement used for testing. Allows unit tests to run without a real MessageBus instance.

## G

**GUI** — Graphical User Interface.

**GUIInterface** — The Python API that skills use to display content (`self.gui.*` methods). Not to be confused with the GUI service.

**GUI Service** — The ovos-gui daemon that manages namespaces, templates, and routes messages between skills and adapters. Implements `GUIService` class.

## H

**Handler** — See [Event Handler](#event-handler).

**Home Screen** — The default page shown when no skill is active. Usually displays weather, time, or idle content.

## I

**Idle Display** — The screen shown when OVOS is not actively handling an intent. Usually shows time, weather, or a screensaver.

**Intent** — A structured request from a user (e.g., "what's the weather"). Resolved by the skill system and passed to a handler method.

**Intent Handler** — A skill method decorated with `@intent_handler` that processes a specific intent type.

## J

**JSON** — JavaScript Object Notation. Used for all data payloads on the MessageBus.

## K

**Key** — A named field in a data dictionary. Example: `"current_temp"` is a key in weather template data.

## L

**Legacy** — Outdated code or patterns that are maintained for backward compatibility.

**List** — A sequence of items, often rendered as a scrollable list in the GUI.

## M

**Message** — A JSON object sent on the MessageBus with `type`, `data`, and `context` fields.

**MessageBus** — A WebSocket pub/sub system that enables communication between OVOS components (core, skills, adapters, etc.). Default port: 8181.

**Mock** — A fake object used in tests to simulate real behavior without dependencies.

## N

**Namespace** — A logical "window" or "app space" for a skill or system component. Namespaces contain pages. Example: `skill-weather.openvoiceos`.

**Notification** — A temporary message displayed to the user, often with a dismiss button.

## O

**OPM** — OVOS Plugin Manager. System for discovering and loading plugins via entry points.

**OVOS** — Open Voice Operating System. The platform this documentation describes.

## P

**Page** — A single screen or view within a namespace. Pages have a name, template type, and data.

**Persistent** — A property of pages that determines whether they survive a skill restart.

**Plugin** — A loadable module that extends OVOS functionality. Examples: TTS plugins, STT plugins, GUI adapters.

**Provider** — An entity that provides services or plugins.

## Q

**QML** — Qt Modeling Language. Declarative language used for UI in the Qt5 GUI adapter.

## R

**Renderer** — Same as [Adapter](#adapter) — a component that renders GUI templates.

**Request** — A message sent from a skill asking the GUI system to show content.

**Route** — Mapping of a namespace to a specific adapter (e.g., "show music skill on web adapter").

## S

**Session** — A connection between a user (via adapter) and OVOS. Session data is temporary state shared during that connection.

**Session Data** — Temporary state shared between a skill and its adapter(s). Examples: user selections, scroll position, form input.

**Skill** — An OVOS plugin that handles intents and provides functionality. Skills use the GUI system to display content via templates.

**Skill ID** — A unique identifier for a skill: `<creator>-<name>.<domain>`. Example: `openvoiceos-weather.openvoiceos`.

**Skill Manifest** — Metadata file (often `skill.json` or embedded in code) describing a skill's capabilities.

**State** — Current condition of a system or component. Example: is the music player playing or paused?

**State Machine** — A system that transitions between defined states based on events.

## T

**Template** — A standardized data structure for a type of content. OVOS provides 21 templates (weather, music, news, etc.). Skills pass template data to the GUI system; adapters render it.

**TUI** — Text User Interface. A terminal-based GUI for debugging without a graphical adapter.

**Type** — The category of a message, event, or data structure. Example: `gui.request_page` is a message type.

## U

**Utterance** — Spoken or typed words from a user that are processed as an intent.

**User Input** — Data sent from an adapter to a skill when a user interacts with the display (clicks a button, selects an item, etc.).

## V

**Validation** — Checking that data meets expected criteria (correct type, required fields, etc.).

**View** — A visual component or screen. Often used interchangeably with [Page](#page).

## W

**WebSocket** — Network protocol for persistent, bidirectional communication. Used by the MessageBus.

**Widget** — A GUI component like a button, slider, or text box.

## X

(No common GUI terms start with X.)

## Y

(No common GUI terms start with Y.)

## Z

(No common GUI terms start with Z.)

---

## Acronyms

| Acronym | Meaning |
|---------|---------|
| API | Application Programming Interface |
| CPU | Central Processing Unit |
| E2E | End-to-End |
| GUI | Graphical User Interface |
| HTML | HyperText Markup Language |
| JSON | JavaScript Object Notation |
| OPM | OVOS Plugin Manager |
| OVOS | Open Voice Operating System |
| QML | Qt Modeling Language |
| REST | Representational State Transfer |
| TUI | Text User Interface |
| UI | User Interface |
| WS | WebSocket |
| XML | eXtensible Markup Language |

---

## See Also

- **[Core Concepts](concepts.md)** — More detailed explanations of key terminology
- **[Architecture](architecture.md)** — System design and how components interact
- **[FAQ](../FAQ.md)** — Common questions
