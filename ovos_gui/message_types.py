"""GUI MessageBus protocol message type definitions.

This module defines all standardized message types used in the OpenVoiceOS GUI
communication protocol between skills, core, and GUI adapters.

Message types are organized by functional domain:
- Connection: Client lifecycle and negotiation
- Namespaces: Skill session management
- Pages: Display and template rendering
- Session: Interactive state between skill and adapter
- Events: System and skill events
- ShellFeatures: Brightness, color scheme, notifications, widgets, config
"""

from enum import Enum


class GUIMessageType(str, Enum):
    """Enumeration of all valid GUI message types in OpenVoiceOS.

    Using string Enum allows direct comparison with message.msg_type strings
    while providing type safety and IDE autocomplete.
    """

    # ==================== CONNECTION & LIFECYCLE ====================
    """Client-adapter handshake and availability signals."""

    OVOS_GUI_CONNECTED = "mycroft.gui.connected"
    """Client announces connection to adapter.

    Sent by: Qt GUI client, Web adapter, or any GUI adapter
    Data: {session_id, adapter_type}
    """

    OVOS_GUI_UNAVAILABLE = "mycroft.gui.unavailable"
    """Adapter signals GUI is unavailable (shutdown, disconnect).

    Sent by: GUI adapter
    Response to: Skill requests when adapter offline
    """

    # ==================== NAMESPACE MANAGEMENT ====================
    """Skill window/session lifecycle in the GUI stack."""

    GUI_PAGE_SHOW = "gui.page.show"
    """Display a template-based page in a namespace.

    Sent by: Skills via ovos_workshop.gui.show_*() methods
    Data: {
        page_names: [str],      # List of SYSTEM_* template names
        __from: str,            # Skill ID (namespace)
        __idle: int,            # Idle display timeout (seconds)
        __duration: int,        # Display duration override
        __persistent: bool,     # Persist across navigation
        [template_data]: ...    # Template-specific fields (current_temp, etc)
    }
    """

    GUI_CLEAR_NAMESPACE = "gui.clear.namespace"
    """Remove entire namespace from display stack (legacy name).

    Sent by: Core or skills
    Data: {__from: skill_id}

    Note: Deprecated in favor of OVOS_GUI_SCREEN_CLOSE
    """

    OVOS_GUI_SCREEN_CLOSE = "ovos.gui.screen.close"
    """Remove namespace from display and deactivate it.

    Sent by: Core, skills, or adapter (when user navigates away)
    Data: {__from: skill_id}
    Replaces: GUI_CLEAR_NAMESPACE (preferred form)
    """

    GUI_NAMESPACE_REMOVED = "gui.namespace.removed"
    """Notification that namespace was removed from stack.

    Sent by: NamespaceManager (ovos-gui)
    Response to: GUI_CLEAR_NAMESPACE or OVOS_GUI_SCREEN_CLOSE
    """

    GUI_NAMESPACE_DISPLAYED = "gui.namespace.displayed"
    """Notification that namespace was activated/brought to front.

    Sent by: NamespaceManager (ovos-gui)
    Data: {__from: skill_id}
    """

    # ==================== SESSION DATA ====================
    """Temporary state shared between skill and adapter(s)."""

    GUI_VALUE_SET = "gui.value.set"
    """Update session data in active namespace.

    Sent by: Skills via self.gui.set_context()
    Data: {__from: skill_id, [key: value]: ...}
    Note: Keys prefixed with __ are reserved by the system
    """

    # Session list operations (for adapter list models)
    MYCROFT_SESSION_SET = "mycroft.session.set"
    """Set session variable (legacy, maps to GUI_VALUE_SET)."""

    MYCROFT_SESSION_DELETE = "mycroft.session.delete"
    """Delete session variable."""

    MYCROFT_SESSION_LIST_INSERT = "mycroft.session.list.insert"
    """Insert item into session list."""

    MYCROFT_SESSION_LIST_UPDATE = "mycroft.session.list.update"
    """Update item in session list."""

    MYCROFT_SESSION_LIST_MOVE = "mycroft.session.list.move"
    """Move item within session list."""

    MYCROFT_SESSION_LIST_REMOVE = "mycroft.session.list.remove"
    """Remove item from session list."""

    # ==================== PAGE INTERACTION ====================
    """User interactions forwarded from adapter to skill."""

    GUI_PAGE_INTERACTION = "gui.page_interaction"
    """User interacted with displayed page (tapped, scrolled, etc).

    Sent by: Adapter (e.g., Qt GUI when user touches screen)
    Data: {skill_id: str, page_number: int}
    """

    GUI_PAGE_GAINED_FOCUS = "gui.page_gained_focus"
    """User navigated to a specific page in the namespace.

    Sent by: Adapter
    Data: {__from: skill_id, page_number: int}
    """

    # ==================== STATUS EVENTS ====================
    """System status events broadcast to all adapters."""

    MYCROFT_RECOGNIZER_LOOP_RECORD_BEGIN = "mycroft.recognizer_loop.record_begin"
    """STT recording started."""

    MYCROFT_RECOGNIZER_LOOP_RECORD_END = "mycroft.recognizer_loop.record_end"
    """STT recording ended."""

    MYCROFT_RECOGNIZER_LOOP_UTTERANCE = "mycroft.recognizer_loop.utterance"
    """User utterance captured by STT."""

    MYCROFT_RECOGNIZER_LOOP_WAKE_WORD = "mycroft.recognizer_loop.wake_word"
    """Wakeword detected."""

    MYCROFT_AUDIO_OUTPUT_START = "mycroft.audio_output.start"
    """Audio playback started (TTS, skill audio, etc)."""

    MYCROFT_AUDIO_OUTPUT_END = "mycroft.audio_output.end"
    """Audio playback ended."""

    MYCROFT_SKILL_HANDLER_START = "mycroft.skill.handler.start"
    """Skill intent handler started executing."""

    MYCROFT_SKILL_HANDLER_ERROR = "mycroft.skill.handler.error"
    """Skill intent handler raised an exception."""

    # ==================== SKILL INTERACTION RESPONSES ====================
    """Bidirectional interaction between skill and adapter."""

    # Confirmation interaction
    SKILL_CONFIRM_RESPONSE = "{skill_id}.confirm.response"
    """Response to a confirmation dialog interaction.

    Pattern: <skill_id>.confirm.response
    Data: {result: bool}
    """

    # Selection interaction
    SKILL_SELECT_RESPONSE = "{skill_id}.select.response"
    """Response to a selection/list interaction.

    Pattern: <skill_id>.select.response
    Data: {result: str|int}
    """

    # ==================== SHELL FEATURES (GUI EXTENSIONS) ====================
    """First-class GUI extensions for system features and appearance.

    These were historically called "GUI extensions" but are now considered
    part of the main GUI specification. All adapters should support them
    to the extent their platform allows.
    """

    # Brightness control
    GUI_BRIGHTNESS_SET = "gui.brightness.set"
    """Set screen brightness level.

    Data: {brightness: int (0-100)}
    """

    GUI_BRIGHTNESS_GET = "gui.brightness.get"
    """Query current screen brightness.

    Response: GUI_BRIGHTNESS_SET with current value
    """

    GUI_BRIGHTNESS_AUTO_DIM_SET = "gui.brightness.auto_dim.set"
    """Enable/disable automatic brightness dimming.

    Data: {enabled: bool}
    """

    GUI_BRIGHTNESS_NIGHT_MODE_SET = "gui.brightness.night_mode.set"
    """Enable/disable night mode (reduced blue light, etc).

    Data: {enabled: bool}
    """

    # Color scheme management
    GUI_COLOR_SCHEME_SET = "gui.color_scheme.set"
    """Set color scheme/theme.

    Data: {scheme: str}
    """

    GUI_COLOR_SCHEME_GET = "gui.color_scheme.get"
    """Query available color schemes.

    Response: List of available scheme names
    """

    # Notifications
    GUI_NOTIFICATION_SET = "gui.notification.set"
    """Display a system notification.

    Data: {
        title: str,
        message: str,
        duration: int (ms),
        type: str (info|warning|error|success)
    }
    """

    GUI_NOTIFICATION_CLEAR = "gui.notification.clear"
    """Clear active notifications."""

    # Custom widgets
    GUI_WIDGET_DISPLAY = "gui.widget.display"
    """Display a custom widget.

    Data: {widget_id: str, config: dict}
    """

    GUI_WIDGET_REMOVE = "gui.widget.remove"
    """Remove a custom widget.

    Data: {widget_id: str}
    """

    # Configuration UI
    GUI_CONFIG_LIST_GET = "gui.config.list.get"
    """Get list of available configuration modules."""

    GUI_CONFIG_GET = "gui.config.get"
    """Get configuration for a module.

    Data: {module: str}
    """

    GUI_CONFIG_SET = "gui.config.set"
    """Set configuration for a module.

    Data: {module: str, config: dict}
    """

    # ==================== EVENTS ====================
    """Skill-defined custom events."""

    GUI_EVENT_SEND = "gui.event.send"
    """Send arbitrary event from skill.

    Data: {event: str, [data]: ...}
    """

    MYCROFT_EVENTS_TRIGGERED = "mycroft.events.triggered"
    """Event triggered and handled."""

    # ==================== RESERVED / LEGACY ====================
    """Deprecated message types kept for backward compatibility."""

    MYCROFT_GUI_AVAILABLE = "mycroft.gui.available"
    """Deprecated: Use OVOS_GUI_CONNECTED"""

    MYCROFT_GUI_UNAVAILABLE = "mycroft.gui.unavailable"
    """Deprecated: Use OVOS_GUI_UNAVAILABLE"""

    MYCROFT_GUI_LIST_INSERT = "mycroft.gui.list.insert"
    """Deprecated: Use MYCROFT_SESSION_LIST_INSERT"""

    MYCROFT_GUI_LIST_MOVE = "mycroft.gui.list.move"
    """Deprecated: Use MYCROFT_SESSION_LIST_MOVE"""

    MYCROFT_GUI_LIST_REMOVE = "mycroft.gui.list.remove"
    """Deprecated: Use MYCROFT_SESSION_LIST_REMOVE"""

    MYCROFT_SYSTEM_ACTIVE_SKILLS = "mycroft.system.active_skills"
    """Reserved: System-level active skills list (not user-exposed)."""

    def __str__(self) -> str:
        """Return the message type string value."""
        return self.value

    @classmethod
    def for_skill(cls, skill_id: str, interaction_type: str) -> str:
        """Generate skill-specific interaction response message type.

        Args:
            skill_id: The skill identifier
            interaction_type: Type of interaction (confirm, select, etc)

        Returns:
            Full message type string (e.g. "skill-weather.openvoiceos.confirm.response")
        """
        return f"{skill_id}.{interaction_type}.response"
