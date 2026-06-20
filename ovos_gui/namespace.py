# Copyright 2022 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Defines the API for the GUI service.

Manages what is displayed on a device with a screen using a LIFO stack of
"active" namespaces (e.g. skills). At the bottom of the stack is the namespace
for the idle screen skill (if one is specified in the device configuration).
The namespace at the top of the stack represents what is visible on the device.
When a skill is finished displaying information, its namespace is removed from
the top of the stack, displaying the previously active namespace.

The persistence of a namespace indicates how long it stays in the active stack.
A numeric persistence is the number of seconds the namespace stays active; a
``True`` persistence keeps it active until the skill removes it.

Routing is keyed solely by ``session_id``: every GUI message carries a session
in ``message.context["session"]``. A shared/multi-room screen is expressed by
clients sharing the same ``session_id`` (the on-device default is
``session_id == "default"``). There is no separate location dimension. Each
session keeps its own namespace stack; the ``session_id`` is forwarded to every
adapter so adapters can target the matching client(s).
"""
from threading import Lock, Timer
from typing import List, Union, Optional, Dict

from ovos_bus_client import Message, MessageBusClient
from ovos_spec_tools import SpecMessage
from ovos_utils.log import LOG

namespace_lock = Lock()

RESERVED_KEYS = ['__from', '__idle']


def _validate_page_message(message: Message) -> bool:
    """
    Validates the contents of the message data for page add/remove messages.

    @param message: Message with request to add/remove one or more pages
        from a namespace.
    @returns: True if request is valid, else False
    """
    valid = (
            "page_names" in message.data
            and "__from" in message.data
            and isinstance(message.data["page_names"], list)
    )
    if not valid:
        if message.msg_type == "gui.page.show":
            action = "shown"
        else:
            action = "removed"
        LOG.error(f"Page will not be {action} due to malformed data in the"
                  f" {message.msg_type} message")
    return valid


class Namespace:
    """A grouping mechanism for related GUI templates and data.

    In the majority of cases, a namespace represents a skill. This class defines
    an API to manage a namespace and its session data. All display goes through
    standardized templates (SYSTEM_*).

    Attributes:
        skill_id: the name of the Namespace, generally the skill ID
        persistent: indicates whether or not the namespace persists for a
            period of time or until the namespace is removed.
        duration: if the namespace persists for a period of time, this is the
            number of seconds of persistence
        data: a key/value pair representing the data used to populate the GUI
    """

    def __init__(self, skill_id: str):
        self.skill_id = skill_id
        self.persistent = False
        self.duration = 30
        self.data = dict()
        self.session_set = False

    def add(self):
        """
        Adds this namespace to the list of active namespaces.
        State change is notified to adapters via NamespaceManager.
        """
        LOG.info(f"GUI PROTOCOL - Adding \"{self.skill_id}\" to active namespaces")

    def activate(self, position: int):
        """
        Activate this namespace if it's already in the list of active namespaces.
        @param position: position to move this namespace FROM
        """
        LOG.info(f"GUI PROTOCOL - Activating namespace \"{self.skill_id}\"")

    def remove(self, position: int):
        """
        Removes this namespace from the list of active namespaces and clears
        any session data.

        @param position: position to remove this namespace FROM
        """
        LOG.info(f"GUI PROTOCOL - Removing \"{self.skill_id}\" from active namespaces")
        # unload the data first before removing the namespace
        for key in list(self.data.keys()):
            self.unload_data(key)

        self.session_set = False
        self.data = dict()

    def load_data(self, name: str, value: str):
        """
        Adds or changes the value of a namespace data attribute.

        Args:
            name: The name of the attribute
            value: The attribute's value
        """
        LOG.info(f"GUI PROTOCOL - Loading \"{self.skill_id}\" data -- {name} : {value} ")

    def unload_data(self, name: str):
        """
        Delete data from the namespace.

        @param name: name of property to delete
        """
        LOG.info(f"GUI PROTOCOL - Unloading namespace \"{self.skill_id}\" key: {name}")
        if name in self.data:
            del self.data[name]

    def get_position_of_last_item_in_data(self) -> int:
        """
        Get the position of the last item
        """
        return len(self.data) - 1

    def set_persistence(self, skill_type: str):
        """
        Sets the duration of the namespace's time in the active list.

        @param skill_type: if skill type is idleDisplaySkill, the namespace will
            always persist.  Otherwise, the namespace persists for a default duration.
        """
        if skill_type == "idleDisplaySkill":
            self.persistent = True
            self.duration = 0
        else:
            self.persistent = False
            self.duration = 30

        LOG.info(
            f"GUI PROTOCOL - Set persistence for \"{self.skill_id}\" -- "
            f"persistent: {self.persistent}, duration: {self.duration}s")


class GUISession:
    """Represents a single GUI session (a screen or a group of shared screens).

    Each session maintains its own stack of active namespaces, loaded namespace
    data, and timers. Clients that share a ``session_id`` share this session.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.loaded_namespaces: Dict[str, Namespace] = dict()
        self.active_namespaces: List[Namespace] = list()
        self.remove_namespace_timers: Dict[str, Timer] = dict()


class NamespaceManager:
    """
    Manages the active namespace stack and the content of namespaces.

    Attributes:
        core_bus: client for communicating with the core message bus
        adapters: loaded GUI adapter plugins
        sessions: dictionary of active sessions (session_id -> GUISession)
    """

    def __init__(self, core_bus: MessageBusClient, adapters: Optional[List] = None):
        self.core_bus = core_bus
        self.adapters: List = adapters or []
        self.sessions: Dict[str, GUISession] = dict()
        self._define_message_handlers()

    def get_session(self, session_id: str) -> GUISession:
        """Retrieve a session by ID, creating it if necessary.

        Args:
            session_id: Routing key for the session.
        Returns:
            The GUISession object.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = GUISession(session_id)
        return self.sessions[session_id]

    @staticmethod
    def _session_id(message: Optional[Message]) -> str:
        """Extract the routing ``session_id`` from a message.

        The routing identifier is the ``session_id``; shared screens share a
        ``session_id``. Defaults to ``"default"`` for on-device displays.
        """
        ctx = message.context if message else {}
        session = ctx.get("session", {})
        return session.get("session_id") or "default"

    # ====== State Query API for Adapters ======

    def get_active_namespace(self, session_id: str = "default") -> Optional[Namespace]:
        """Get the currently active (top-of-stack) namespace for a session.

        Allows adapters to query which namespace is currently visible and
        recover state after a crash.

        Args:
            session_id: Session identifier (default: "default" for single-screen)

        Returns:
            Active Namespace object if one exists, else None
        """
        session = self.sessions.get(session_id)
        if session and session.active_namespaces:
            return session.active_namespaces[0]  # Top of stack is index 0
        return None

    def get_namespace_data(self, namespace_name: str, session_id: str = "default") -> Optional[dict]:
        """Get current session data for a namespace.

        Args:
            namespace_name: Skill ID or namespace name
            session_id: Session identifier

        Returns:
            Copy of the session data dict if the namespace exists, else None
        """
        session = self.sessions.get(session_id)
        if session:
            namespace = session.loaded_namespaces.get(namespace_name)
            if namespace:
                return namespace.data.copy()  # copy prevents external mutation
        return None

    def get_all_sessions(self) -> List[str]:
        """Get list of all active session IDs.

        Returns:
            List of session_id strings
        """
        return list(self.sessions.keys())

    def is_namespace_active(self, namespace_name: str, session_id: str = "default") -> bool:
        """Check if a namespace is currently visible (top of active stack).

        Args:
            namespace_name: Skill ID or namespace name
            session_id: Session identifier

        Returns:
            True if namespace is currently displayed, False otherwise
        """
        active_ns = self.get_active_namespace(session_id)
        if active_ns:
            return active_ns.skill_id == namespace_name
        return False

    def _define_message_handlers(self):
        """
        Defines event handlers for core messagebus.
        """
        self.core_bus.on("gui.clear.namespace", self.handle_clear_namespace)
        self.core_bus.on("gui.page.show", self.handle_show_page)
        self.core_bus.on("gui.status.request", self.handle_status_request)
        self.core_bus.on("gui.value.set", self.handle_set_value)
        self.core_bus.on("gui.page_interaction", self.handle_page_interaction)
        self.core_bus.on("gui.page_gained_focus", self.handle_page_gained_focus)
        self.core_bus.on("mycroft.gui.screen.close", self.handle_namespace_global_back)
        self._define_messages_to_forward()

    def _define_messages_to_forward(self):
        """Messages from the core bus to be forwarded to GUI clients."""
        messages_to_forward = [
            # Core
            "ovos.utterance.handled",
            "ovos.utterance.cancelled",
            "mycroft.skill.handler.start",
            "mycroft.skill.handler.complete",
            "complete_intent_failure",
            # Audio Service
            "speak",
            "recognizer_loop:audio_output_start",
            "recognizer_loop:audio_output_end",
            # Speech Service
            SpecMessage.LISTENER_SLEEP,
            "recognizer_loop:wake_up",
            SpecMessage.LISTENER_AWOKEN,
            "recognizer_loop:utterance",
            "recognizer_loop:wakeword",
            "recognizer_loop:recognition_unknown",
            SpecMessage.LISTENER_RECORD_STARTED,
            SpecMessage.LISTENER_RECORD_ENDED,
            # Enclosure commands for eyes
            "enclosure.eyes.on",
            "enclosure.eyes.off",
            "enclosure.eyes.blink",
            "enclosure.eyes.narrow",
            "enclosure.eyes.look",
            "enclosure.eyes.color",
            "enclosure.eyes.level",
            "enclosure.eyes.volume",
            "enclosure.eyes.spin",
            "enclosure.eyes.timedspin",
            "enclosure.eyes.reset",
            "enclosure.eyes.setpixel",
            "enclosure.eyes.fill",
            # Enclosure commands for mouth
            "enclosure.mouth.events.activate",
            "enclosure.mouth.events.deactivate",
            "enclosure.mouth.talk",
            "enclosure.mouth.think",
            "enclosure.mouth.listen",
            "enclosure.mouth.smile",
            "enclosure.mouth.viseme",
            "enclosure.mouth.viseme_list",
            # Mouth/matrix display
            "enclosure.mouth.reset",
            "enclosure.mouth.text",
            "enclosure.mouth.display",
            "enclosure.weather.display"
        ]
        for msg in messages_to_forward:
            self.core_bus.on(msg, self.forward_to_gui)

    def _safe_call(self, adapter, method_name, *args, **kwargs):
        """Invoke an adapter hook safely.

        Missing methods are ignored. Any exception raised by the adapter is
        logged so a broken adapter cannot crash the service or block the other
        adapters. Signature errors are surfaced (logged) rather than silently
        retried with fewer arguments.
        """
        method = getattr(adapter, method_name, None)
        if method:
            try:
                method(*args, **kwargs)
            except Exception:
                LOG.exception(f"Error in {adapter.__class__.__name__}.{method_name}")

    def forward_to_gui(self, message: Message):
        """
        Forward a core Message status event to registered adapters.

        Status events are system-wide signals; adapters typically broadcast them
        to all connected clients regardless of session.

        @param message: Core message to forward
        """
        LOG.info(f"GUI PROTOCOL - Forwarding status event '{message.msg_type}'")
        session_id = self._session_id(message)
        for adapter in self.adapters:
            self._safe_call(adapter, "on_status_event", message.msg_type,
                            message.data, session_id)

    def handle_clear_namespace(self, message: Message):
        """
        Handles a request to remove a namespace.
        @param message: the message requesting namespace removal
        """
        try:
            namespace_name = message.data['__from']
        except KeyError:
            LOG.error(
                "Request to delete namespace failed: no namespace specified"
            )
        else:
            session_id = self._session_id(message)
            session = self.get_session(session_id)
            if session.loaded_namespaces.get(namespace_name):
                with namespace_lock:
                    self._remove_namespace(namespace_name, session, session_id)

    @staticmethod
    def _parse_persistence(persistence: Optional[Union[int, bool]]) -> \
            (bool, int):
        """
        Parse a persistence spec into persist and duration.
        @param persistence: message.data["__idle"] spec
        @return: bool persistence, int duration
        """
        if isinstance(persistence, float):
            persistence = round(persistence)
        if isinstance(persistence, bool):
            return persistence, 0
        elif isinstance(persistence, int):
            if persistence < 0:
                raise ValueError("Requested negative persistence")
            return False, persistence
        else:
            # Defines default behavior as displaying for 30 seconds
            return False, 30

    def _dispatch_template_to_adapters(self, template: str, skill_id: str,
                                       data: dict, session_id: str):
        """Call matching handler on every loaded adapter for a SYSTEM_* template.

        Args:
            template: PageTemplates value, e.g. ``"SYSTEM_weather"``.
            skill_id: Namespace / skill that requested the display.
            data:     Current session data for the namespace.
            session_id: Routing identifier (shared screens share a session_id).
        """
        for adapter in self.adapters:
            try:
                adapter.dispatch_template(template, skill_id, data, session_id)
            except Exception:
                LOG.exception(
                    f"Error dispatching template '{template}' to adapter "
                    f"{adapter.__class__.__name__}"
                )

    def handle_show_page(self, message: Message):
        """
        Handles a request to show one or more pages on the screen.
        @param message: the message containing the page show request
        """
        message_is_valid = _validate_page_message(message)
        if not message_is_valid:
            LOG.error(f"invalid request: {message.data}")
            return

        namespace_name = message.data["__from"]
        page_ids_to_show = message.data.get('page_names')
        persistence = message.data["__idle"]
        show_index = message.data.get("index", 0)

        LOG.debug(f"Got {namespace_name} request to show: {page_ids_to_show} at index: {show_index}")

        session_id = self._session_id(message)
        session = self.get_session(session_id)

        # All page shows must use SYSTEM_* templates (no legacy QML path)
        if not page_ids_to_show:
            LOG.error(f"Namespace '{namespace_name}' requested show with no page_names")
            return

        if not page_ids_to_show[0].startswith("SYSTEM_"):
            LOG.error(
                f"Namespace '{namespace_name}' sent non-template page name: {page_ids_to_show[0]}. "
                f"All GUI display must use SYSTEM_* templates. Custom QML is not supported."
            )
            return

        # Template-based routing: dispatch all templates to adapters
        namespace = self._ensure_namespace_exists(namespace_name, session)
        data = {k: v for k, v in namespace.data.items()}
        for template in page_ids_to_show:
            self._dispatch_template_to_adapters(template, namespace_name, data, session_id)

        # Activate namespace (updates internal stack state)
        with namespace_lock:
            if not session.active_namespaces or session.active_namespaces[0].skill_id != namespace_name:
                self._activate_namespace(namespace_name, session, session_id)
            self._update_namespace_persistence(persistence, session)

    def _activate_namespace(self, namespace_name: str, session: GUISession,
                            session_id: str):
        """
        Instructs the GUI to load a namespace and its associated data.

        @param namespace_name: the name of the namespace to load
        @param session: the session affected (state object)
        @param session_id: routing identifier
        """
        namespace = self._ensure_namespace_exists(namespace_name, session)

        if namespace in session.active_namespaces:
            namespace_position = session.active_namespaces.index(namespace)
            namespace.activate(namespace_position)
            if namespace_position != 0:
                LOG.info(f"Activating namespace: {namespace_name} for session {session.session_id}")
                session.active_namespaces.insert(
                    0, session.active_namespaces.pop(namespace_position)
                )
        else:
            LOG.info(f"New namespace: {namespace_name} for session {session.session_id}")
            namespace.add()
            session.active_namespaces.insert(0, namespace)
            # sync initial state
            for key, value in namespace.data.items():
                namespace.load_data(key, value)

        self._emit_namespace_displayed_event(session)
        # Notify adapters of namespace activation
        for adapter in self.adapters:
            self._safe_call(adapter, "on_namespace_activated", namespace_name, session_id)

    def _ensure_namespace_exists(self, namespace_name: str, session: GUISession) -> Namespace:
        """
        Retrieves the requested namespace, creating one if it doesn't exist.
        @param namespace_name: the name of the namespace being retrieved
        @param session: the session affected
        @returns: requested namespace
        """
        namespace = session.loaded_namespaces.get(namespace_name)
        if namespace is None:
            namespace = Namespace(namespace_name)
            session.loaded_namespaces[namespace_name] = namespace

        return namespace

    def _update_namespace_persistence(self, persistence: Union[bool, int], session: GUISession):
        """
        Sets the persistence of the namespace being activated.
        @param persistence: length of time the namespace should be displayed
        @param session: the session affected
        """
        for idx, namespace in enumerate(session.active_namespaces):
            if idx:
                if not namespace.persistent:
                    self._remove_namespace(namespace.skill_id, session, session.session_id)
            else:
                if namespace.persistent != persistence:
                    LOG.info(f"Setting namespace '{namespace.skill_id}' persistence to: {persistence}")
                    namespace.persistent = persistence

                namespace.set_persistence(skill_type="genericSkill")
                if isinstance(persistence, int) and not isinstance(persistence, bool):
                    namespace.duration = persistence

                # check if there is a scheduled remove_namespace_timer
                # and cancel it
                if namespace.persistent and namespace.skill_id in \
                        session.remove_namespace_timers:
                    session.remove_namespace_timers[namespace.skill_id].cancel()
                    self._del_namespace_in_remove_timers(namespace.skill_id, session)

                if not namespace.persistent:
                    self._schedule_namespace_removal(namespace, session)

                session.active_namespaces[idx] = namespace

    def _schedule_namespace_removal(self, namespace: Namespace, session: GUISession):
        """
        Uses a timer thread to remove the namespace.
        @param namespace: the namespace to be removed
        @param session: the session affected
        """
        # Before removing check if there isn't already a timer for this namespace
        if namespace.skill_id in session.remove_namespace_timers:
            return

        remove_namespace_timer = Timer(
            namespace.duration,
            self._remove_namespace_via_timer,
            args=(namespace.skill_id, session.session_id)
        )
        LOG.info(f"Removal of namespace {namespace.skill_id} in session {session.session_id} in "
                 f"{namespace.duration} seconds")
        remove_namespace_timer.start()
        session.remove_namespace_timers[namespace.skill_id] = remove_namespace_timer

    def _remove_namespace_via_timer(self, namespace_name: str, session_id: str):
        """
        Removes a namespace and the corresponding timer instance.
        @param namespace_name: name of namespace to remove
        @param session_id: ID of the session
        """
        session = self.get_session(session_id)
        self._remove_namespace(namespace_name, session, session_id)
        self._del_namespace_in_remove_timers(namespace_name, session)

    def _remove_namespace(self, namespace_name: str, session: GUISession,
                          session_id: str):
        """
        Removes a namespace from the active namespace stack.
        @param namespace_name: name of namespace to remove
        @param session: the session affected (state object)
        @param session_id: routing identifier
        """
        # Remove all timers associated with the namespace
        if namespace_name in session.remove_namespace_timers:
            session.remove_namespace_timers[namespace_name].cancel()
            self._del_namespace_in_remove_timers(namespace_name, session)

        namespace: Namespace = session.loaded_namespaces.get(namespace_name)
        if namespace is not None and namespace in session.active_namespaces:
            LOG.info(f"Removing namespace {namespace_name} from session {session.session_id}")
            self.core_bus.emit(Message("gui.namespace.removed",
                                       data={"skill_id": namespace.skill_id},
                                       context={"session": {"session_id": session_id}}))
            namespace_position = session.active_namespaces.index(namespace)
            namespace.remove(namespace_position)
            session.active_namespaces.remove(namespace)
            # Notify adapters of namespace deactivation
            for adapter in self.adapters:
                self._safe_call(adapter, "on_namespace_deactivated", namespace_name, session_id)

        self._emit_namespace_displayed_event(session)

    def _emit_namespace_displayed_event(self, session: GUISession):
        """
        Emit a `gui.namespace.displayed` Message to notify core of changes.
        """
        if session.active_namespaces:
            displaying_namespace = session.active_namespaces[0]
            message_data = dict(skill_id=displaying_namespace.skill_id)
            self.core_bus.emit(
                Message("gui.namespace.displayed", data=message_data,
                        context={"session": {"session_id": session.session_id}})
            )

    def handle_status_request(self, message: Message):
        """
        Handles a GUI status request by replying with the connection status.
        Checks all loaded adapters; returns True if any adapter has a connected client.
        @param message: the request for status of the GUI
        """
        gui_connected = any(
            getattr(adapter, 'any_client_connected', lambda: False)()
            for adapter in self.adapters
        ) if self.adapters else False
        reply = message.reply(
            "gui.status.request.response", dict(connected=gui_connected)
        )
        self.core_bus.emit(reply)

    def handle_set_value(self, message: Message):
        """
        Handles a request to set the value of namespace data attributes.
        @param message: the request to set attribute values
        """
        try:
            namespace_name = message.data['__from']
        except KeyError:
            LOG.error(
                "Request to set gui attribute value failed: no "
                "namespace specified"
            )
        else:
            session_id = self._session_id(message)
            session = self.get_session(session_id)
            with namespace_lock:
                self._update_namespace_data(namespace_name, message.data, session)
            # Notify adapters of the session data update
            filtered = {k: v for k, v in message.data.items() if k not in RESERVED_KEYS}
            for adapter in self.adapters:
                self._safe_call(adapter, "on_session_update", namespace_name, filtered, session_id)

    def _update_namespace_data(self, namespace_name: str, data: dict, session: GUISession):
        """
        Updates the values of namespace data attributes, unless unchanged.
        @param namespace_name: the name of the namespace to update
        @param data: the name and new value of one or more data attributes
        @param session: the session affected
        """
        namespace = self._ensure_namespace_exists(namespace_name, session)
        for key, value in data.items():
            if key not in RESERVED_KEYS and namespace.data.get(key) != value:
                namespace.data[key] = value
                if namespace in session.active_namespaces:
                    namespace.load_data(key, value)

    def handle_page_interaction(self, message: Message):
        """
        Handles user interaction with the active namespace.
        Reschedules namespace timeout on user interaction.
        @param message: the event sent by the GUI
        """
        namespace_name = message.data.get("skill_id")
        LOG.info(f"GUI interacted with namespace {namespace_name}")

        session_id = self._session_id(message)
        session = self.get_session(session_id)
        namespace = session.loaded_namespaces.get(namespace_name)

        # reschedule namespace timeout on user interaction
        if namespace and not namespace.persistent and \
                session.remove_namespace_timers.get(namespace.skill_id):
            session.remove_namespace_timers[namespace.skill_id].cancel()
            self._del_namespace_in_remove_timers(namespace.skill_id, session)
            self._schedule_namespace_removal(namespace, session)

    def handle_page_gained_focus(self, message: Message):
        """
        Handles focus events from the GUI (template rendering updates).
        @param message: the event sent by the GUI
        """
        namespace_name = message.data.get("skill_id")
        LOG.debug(f"Namespace {namespace_name} received focus event")

        session_id = self._session_id(message)
        session = self.get_session(session_id)

        # Template-only: no page tracking, just verify namespace exists
        namespace = session.loaded_namespaces.get(namespace_name)
        if namespace and namespace in session.active_namespaces:
            LOG.debug(f"Namespace {namespace_name} is active")

    def handle_namespace_global_back(self, message: Optional[Message]):
        """
        Handles global back events from the GUI.
        Removes the current namespace and shows homescreen if none remain.
        @param message: the event sent by the GUI
        """
        session_id = self._session_id(message)
        session = self.get_session(session_id)

        if not session.active_namespaces:
            LOG.debug("received 'back' signal but there are no active namespaces, attempting to show homescreen")
            self.core_bus.emit(Message("mycroft.device.show.idle",
                                       context={"session": {"session_id": session_id}}))
            return

        # Remove the current (top) namespace
        namespace_name = session.active_namespaces[0].skill_id
        self._remove_namespace(namespace_name, session, session_id)

    def _del_namespace_in_remove_timers(self, namespace_name: str, session: GUISession):
        """
        Delete namespace from remove_namespace_timers dict.
        @param namespace_name: name of namespace to be deleted
        @param session: the session affected
        """
        if namespace_name in session.remove_namespace_timers:
            del session.remove_namespace_timers[namespace_name]
