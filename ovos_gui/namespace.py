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
"""Defines the API for the QT GUI.

Manages what is displayed on a device with a touch screen using a LIFO stack
of "active" namespaces (e.g. skills).  At the bottom of the stack is the
namespace for the idle screen skill (if one is specified in the device
configuration).  The namespace for the idle screen skill should never be
removed from the stack.

When a skill with a GUI is triggered by the user, the namespace for that skill
is placed at the top of the stack.  The namespace at the top of the stack
represents the namespace that is visible on the device.  When the skill is
finished displaying information on the screen, it is removed from the top of
the stack.  This will result in the previously active namespace being
displayed.

The persistence of a namespace indicates how long that namespace stays in the
active stack.  A persistence expressed using a number represents how many
seconds the namespace will be active.  A persistence expressed with a True
value will be active until the skill issues a command to remove the namespace.
If a skill with a numeric persistence replaces a namespace at the top of the
stack that also has a numeric persistence, the namespace being replaced will
be removed from the active namespace stack.

The state of the active namespace stack is maintained locally and in the GUI
code.  Changes to namespaces, and their contents, are communicated to the GUI
over the GUI message bus.
"""
import shutil
from os import makedirs
from os.path import join, dirname, isfile, exists
from threading import Event, Lock, Timer
from typing import List, Union, Optional, Dict

from ovos_config.config import Configuration
from ovos_utils.log import LOG, log_deprecation

from ovos_bus_client import Message, MessageBusClient
from ovos_gui.bus import (
    create_gui_service,
    determine_if_gui_connected,
    get_gui_websocket_config,
    send_message_to_gui, GUIWebsocketHandler
)
from ovos_gui.gui_file_server import start_gui_http_server
from ovos_gui.page import GuiPage

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
            "page" in message.data
            and "__from" in message.data
            and isinstance(message.data["page"], list)
    )
    if not valid:
        if message.msg_type == "gui.page.show":
            action = "shown"
        else:
            action = "removed"
        LOG.error(f"Page will not be {action} due to malformed data in the"
                  f" {message.msg_type} message")
    return valid


def _get_idle_display_config() -> str:
    """
    Retrieves the current value of the idle display skill configuration.
    @returns: Configured idle_display_skill (skill_id)
    """
    config = Configuration()
    enclosure_config = config.get("gui") or {}
    idle_display_skill = enclosure_config.get("idle_display_skill")
    LOG.info(f"Configured homescreen: {idle_display_skill}")
    return idle_display_skill


def _get_active_gui_extension() -> str:
    """
    Retrieves the current value of the gui extension configuration.
    @returns: Configured gui extension
    """
    config = Configuration()
    enclosure_config = config.get("gui") or {}
    gui_extension = enclosure_config.get("extension", "generic")
    LOG.info(f"Configured GUI extension: {gui_extension}")
    return gui_extension.lower()


class Namespace:
    """A grouping mechanism for related GUI pages and data.

    In the majority of cases, a namespace represents a skill.  There is a
    SYSTEM namespace for GUI screens that exist outside of skills.  This class
    defines an API to manage a namespace, its pages and its data.  Actions
    are communicated to the GUI message bus.

    Attributes:
        skill_id: the name of the Namespace, generally the skill ID
        persistent: indicates whether or not the namespace persists for a
            period of time or until the namespace is removed.
        duration: if the namespace persists for a period of time, this is the
            number of seconds of persistence
        pages: when the namespace is active, contains all the pages that are
            displayed at the same time
        data: a key/value pair representing the data used to populate the GUI
    """

    def __init__(self, skill_id: str):
        self.skill_id = skill_id
        self.persistent = False
        self.duration = 30
        self.pages: List[GuiPage] = list()
        self.data = dict()
        self.page_number = 0
        self.session_set = False

    @property
    def page_names(self):
        return [page.name for page in self.pages]

    @property
    def active_page(self):
        if len(self.pages):
            if self.page_number >= len(self.pages):
                return None  # TODO - error ?
            return self.pages[self.page_number]
        return None

    def add(self):
        """
        Adds this namespace to the list of active namespaces.
        """
        LOG.info(f"GUI PROTOCOL - Adding \"{self.skill_id}\" to active namespaces")
        message = dict(
            type="mycroft.session.list.insert",
            namespace="mycroft.system.active_skills",
            position=0,
            data=[dict(skill_id=self.skill_id)]
        )
        send_message_to_gui(message)

    def activate(self, position: int):
        """
        Activate this namespace if its already in the list of active namespaces.
        @param position: position to move this namespace FROM
        """
        if not len(self.pages):
            LOG.error(f"Tried to activate namespace without loaded pages: \"{self.skill_id}\"")
            return

        LOG.info(f"GUI PROTOCOL - Activating namespace \"{self.skill_id}\"")
        message = {
            "type": "mycroft.session.list.move",
            "namespace": "mycroft.system.active_skills",
            "from": position,
            "to": 0,
            "items_number": 1
        }
        send_message_to_gui(message)

    def remove(self, position: int):
        """
        Removes this namespace from the list of active namespaces. Also clears
        any session data.
        @param position: position to remove this namespace FROM
        """
        LOG.info(f"GUI PROTOCOL - Removing \"{self.skill_id}\" from active namespaces")
        # unload the data first before removing the namespace
        # use the keys of the data to unload the data
        for key in self.data:
            self.unload_data(key)

        message = dict(
            type="mycroft.session.list.remove",
            namespace="mycroft.system.active_skills",
            position=position,
            items_number=1
        )
        send_message_to_gui(message)
        self.session_set = False
        self.pages = list()
        self.data = dict()

    def load_data(self, name: str, value: str):
        """
        Adds or changes the value of a namespace data attribute.

        Args:
            name: The name of the attribute
            value: The attribute's value
        """
        LOG.info(f"GUI PROTOCOL - Sending \"{self.skill_id}\" data -- {name} : {value} ")
        message = dict(
            type="mycroft.session.set",
            namespace=self.skill_id,
            data={name: value}
        )
        send_message_to_gui(message)

    def unload_data(self, name: str):
        """
        Delete data from the namespace
        @param name: name of property to delete
        """
        LOG.info(f"GUI PROTOCOL - Deleting namespace \"{self.skill_id}\" key: {name}")
        message = dict(
            type="mycroft.session.delete",
            property=name,
            namespace=self.skill_id
        )
        send_message_to_gui(message)

    def get_position_of_last_item_in_data(self) -> int:
        """
        Get the position of the last item
        """
        return len(self.data) - 1

    def set_persistence(self, skill_type: str):
        """
        Sets the duration of the namespace's time in the active list.

        @param skill_type: if skill type is idleDisplaySkill, the namespace will
            always persist.  Otherwise, the namespace will persist based on the
            active page's persistence.
        """
        # check if skill_type is idleDisplaySkill
        if skill_type == "idleDisplaySkill":
            self.persistent = True
            self.duration = 0

        else:
            # get the active page in the namespace
            active_page = self.active_page
            # if type(persistence) == int:
            # Get the duration of the active page if it is not persistent
            if active_page is not None and not active_page.persistent:
                self.persistent = False
                self.duration = active_page.duration

            # elif type(persistence) == bool:
            # Get the persistance of the active page
            elif active_page is not None and active_page.persistent:
                self.persistent = True
                self.duration = 0

            # else use the default duration of 30 seconds
            else:
                LOG.warning(f"No active page, reset persistence for {self.skill_id}")
                self.persistent = False
                self.duration = 30

    def load_pages(self, pages: List[GuiPage], show_index: int = 0):
        """
        Maintains a list of active pages within the active namespace.

        Skills with multiple pages of data can either show all the screens
        at once, allowing the user to swipe back and forth among them, or
        the pages can be loaded one at a time.  The latter is represented by
        a single list item, the former by multiple list items

        @param pages: list of pages to be displayed
        @param show_index: index of page to display (default 0)
        """
        if not pages:
            LOG.error("No pages to load ?")
            return
        if show_index is None:
            LOG.warning(f"Expected int show_index but got `None`. Default to 0")
            show_index = 0
        new_pages = list()
        target_page = pages[show_index]

        for page in pages:
            if page.id not in [p.id for p in self.pages]:
                new_pages.append(page)

        self.pages.extend(new_pages)
        if new_pages:
            self._add_pages(new_pages)
        if show_index >= len(pages):
            LOG.error(
                f"Invalid page index requested: {show_index} , only {len(pages)} pages available for \"{self.skill_id}\"")
        else:
            LOG.info(f"Activating page {show_index} from: {[p.name for p in pages]} for \"{self.skill_id}\"")
            self._activate_page(target_page)

    def _add_pages(self, new_pages: List[GuiPage]):
        """
        Adds one or more pages to the active page list.
        @param new_pages: pages to add to the active page list
        """
        LOG.debug(f"namespace \"{self.skill_id}\" current pages: {self.pages}")
        LOG.debug(f"new_pages={new_pages}")

        # Find position of new page in self.pages
        position = self.pages.index(new_pages[0])
        for client in GUIWebsocketHandler.clients:
            try:
                LOG.debug(f"Updating {client.framework} client")
                client.send_gui_pages(new_pages, self.skill_id, position)
            except Exception as e:
                LOG.exception(f"Error updating {client.framework} client: {e}")

    def focus_page(self, page):
        """
        Returns focus to a page already in the active page list.

        @param page: the page that will gain focus
        """
        # set the index of the page in the self.pages list
        page_index = None
        for i, p in enumerate(self.pages):
            if p.id == page.id:
                # save page index
                page_index = i
                break

        # handle missing page (TODO, can this happen?)
        if page_index is None:
            LOG.warning("tried to activate page missing from pages list, inserting it at index 0")
            page_index = 0
            self.pages.insert(0, page)
        # update page data
        else:
            self.pages[page_index] = page

        if page_index != self.page_number:
            self.page_number = page_index
            LOG.info(f"Focusing page {page.name} -- namespace \"{self.skill_id}\"")

    def _activate_page(self, page: GuiPage):
        """
        Tells mycroft-gui to returns focus to a page

        @param page: the page that will gain focus
        """
        LOG.debug(f"Current pages from _activate_page: {self.pages}")
        self.focus_page(page)

        LOG.info(
            f"GUI PROTOCOL - Sending event 'page_gained_focus' -- page: {page.name} -- namespace: \"{self.skill_id}\"")
        message = dict(
            type="mycroft.events.triggered",
            namespace=self.skill_id,
            event_name="page_gained_focus",
            data={"number": self.page_number}
        )
        send_message_to_gui(message)

    def remove_pages(self, positions: List[int]):
        """
        Deletes one or more pages by index from the active page list.

        @param positions: list of int page positions to remove
        """
        positions.sort(reverse=True)
        for position in positions:
            page = self.pages.pop(position)
            LOG.info(f"GUI PROTOCOL - Deleting {page.name} -- namespace: \"{self.skill_id}\"")
            message = dict(
                type="mycroft.gui.list.remove",
                namespace=self.skill_id,
                position=position,
                items_number=1
            )
            send_message_to_gui(message)

    def page_gained_focus(self, page_number: int):
        """
        Updates the active page in `self.pages`.
        @param page_number: the index of the page that will gain focus
        """
        LOG.info(f"Page {page_number} gained focus -- namespace \"{self.skill_id}\"")
        self.page_number = page_number
        self._activate_page(self.active_page)

    def global_back(self):
        """
        Returns to the previous page in the active page list.
        """
        if self.page_number > 0:  # go back 1 page
            self.remove_pages([self.page_number])
            self.page_gained_focus(self.page_number - 1)


class NamespaceManager:
    """
    Manages the active namespace stack and the content of namespaces.

    Attributes:
        core_bus: client for communicating with the core message bus
        gui_bus: client for communicating with the GUI message bus
        loaded_namespaces: cache of namespaces that have been introduced
        active_namespaces: LIFO stack of namespaces being displayed
        remove_namespace_timers: background process to remove a namespace with
            a persistence expressed in seconds
        idle_display_skill: skill ID of the skill that controls the idle screen
    """

    def __init__(self, core_bus: MessageBusClient):
        self.core_bus = core_bus
        self.gui_bus = create_gui_service(self)
        self.loaded_namespaces: Dict[str, Namespace] = dict()
        self.active_namespaces: List[Namespace] = list()
        self.remove_namespace_timers: Dict[str, Timer] = dict()
        self.idle_display_skill = _get_idle_display_config()
        self.active_extension = _get_active_gui_extension()
        self._system_res_dir = join(dirname(__file__), "res", "gui")
        self._ready_event = Event()
        self.gui_file_server = None
        self.gui_file_path = None  # HTTP Server local path
        self.gui_file_host_path = None  # Docker host path
        self._connected_frameworks: List[str] = list()
        self._init_gui_file_share()
        self._define_message_handlers()

    @property
    def _active_homescreen(self) -> str:
        return Configuration().get('gui', {}).get('idle_display_skill')

    def _init_gui_file_share(self):
        """
        Initialize optional GUI file collection. if `gui_file_path` is
        defined, resources are assumed to be referenced outside this container.
        If `gui_file_server` is defined, resources will be served via HTTP
        """
        config = Configuration().get("gui", {})
        self.gui_file_host_path = config.get("gui_file_host_path")

        # Check for GUI file sharing via HTTP server or mounted host path
        if config.get("gui_file_server") or self.gui_file_host_path:
            from ovos_utils.xdg_utils import xdg_cache_home
            if config.get("server_path"):
                log_deprecation("`server_path` configuration is deprecated. "
                                "Files will always be saved to "
                                "XDG_CACHE_HOME/ovos_gui_file_server", "0.1.0")
            self.gui_file_path = config.get("server_path") or \
                                 join(xdg_cache_home(), "ovos_gui_file_server")
            if config.get("gui_file_server"):
                self.gui_file_server = start_gui_http_server(self.gui_file_path)
            self._upload_system_resources()

    def _define_message_handlers(self):
        """
        Defines event handlers for core messagebus.
        """
        self.core_bus.on("gui.clear.namespace", self.handle_clear_namespace)
        self.core_bus.on("gui.event.send", self.handle_send_event)
        self.core_bus.on("gui.page.delete", self.handle_delete_page)
        self.core_bus.on("gui.page.delete.all", self.handle_delete_all_pages)
        self.core_bus.on("gui.page.show", self.handle_show_page)
        self.core_bus.on("gui.page.upload", self.handle_receive_gui_pages)
        self.core_bus.on("gui.status.request", self.handle_status_request)
        self.core_bus.on("gui.value.set", self.handle_set_value)
        self.core_bus.on("mycroft.gui.connected", self.handle_client_connected)
        self.core_bus.on("gui.page_interaction", self.handle_page_interaction)
        self.core_bus.on("gui.page_gained_focus", self.handle_page_gained_focus)
        self.core_bus.on("mycroft.skills.trained", self.handle_ready)
        self.core_bus.on("mycroft.gui.screen.close", self.handle_namespace_global_back)

    def handle_ready(self, message):
        self._ready_event.set()
        self.core_bus.on("gui.volunteer_page_upload",
                         self.handle_gui_pages_available)

    def handle_gui_pages_available(self, message: Message):
        """
        Handle a skill or plugin advertising that it has GUI pages available to
        upload. If there are connected clients, request pages for each connected
        GUI framework.
        @param message: `gui.volunteer_page_upload` message
        """
        if not any((self.gui_file_host_path, self.gui_file_server)):
            LOG.debug("No GUI file server running or host path configured")
            return

        LOG.debug(f"Requesting resources for {self._connected_frameworks}")
        for framework in self._connected_frameworks:
            skill_id = message.data.get("skill_id")
            self.core_bus.emit(message.reply("gui.request_page_upload",
                                             {'skill_id': skill_id,
                                              'framework': framework},
                                             {"source": "gui",
                                              "destination": ["skills",
                                                              "PHAL"]}))

    def handle_receive_gui_pages(self, message: Message):
        """
        Handle GUI resources from a skill or plugin. Pages are written to
        `self.server_path` which is accessible via a lightweight HTTP server and
        may additionally be mounted to a host path/volume in container setups.
        @param message: Message containing UI resource file contents and meta
            message.data:
                pages: dict page_filename to encoded bytes content;
                    paths are relative to the `framework` directory, so a page
                    for framework `all` could be `qt5/subdir/file.qml` and the
                    equivalent page for framework `qt5` would be
                    `subdir/file.qml`
                framework: `all` if all GUI resources are included, else the
                    specific GUI framework (i.e. `qt5`, `qt6`)
                __from: skill_id of module uploading GUI resources
        """
        for page, contents in message.data["pages"].items():
            try:
                if message.data.get("framework") == "all":
                    # All GUI resources are uploaded
                    resource_base_path = join(self.gui_file_path,
                                              message.data['__from'])
                else:
                    resource_base_path = join(self.gui_file_path,
                                              message.data['__from'],
                                              message.data.get('framework') or
                                              "qt5")
                byte_contents = bytes.fromhex(contents)
                file_path = join(resource_base_path, page)
                LOG.debug(f"writing UI file: {file_path}")
                makedirs(dirname(file_path), exist_ok=True)
                with open(file_path, 'wb+') as f:
                    f.write(byte_contents)
            except Exception as e:
                LOG.exception(f"Failed to write {page}: {e}")
        if message.data["__from"] == self._active_homescreen:
            # Configured home screen skill just uploaded pages, show it again
            self.core_bus.emit(message.forward("homescreen.manager.show_active"))

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
            if self.loaded_namespaces.get(namespace_name):
                with namespace_lock:
                    self._remove_namespace(namespace_name)

    @staticmethod
    def handle_send_event(message: Message):
        """
        Handles a request to send a message to the GUI message bus.
        @param message: the message requesting a message to be sent to the GUI
                message bus.
        """
        try:
            skill_id = message.data.get('__from')
            event = message.data.get('event_name')
            LOG.info(f"GUI PROTOCOL - Sending event '{event}' for namespace: {skill_id}")
            message = dict(
                type='mycroft.events.triggered',
                namespace=skill_id,
                event_name=event,
                data=message.data.get('params')
            )
            send_message_to_gui(message)
        except Exception:
            LOG.exception('Could not send event trigger')

    def handle_delete_all_pages(self, message: Message):
        """
        Handles request to remove all current pages from a namespace.
        @param message: the message requesting page removal
        """
        namespace_name = message.data["__from"]
        except_pages = message.data.get("except") or []

        if except_pages:
            LOG.info(f"Got {namespace_name} request to delete all pages except: {except_pages}")
        else:
            LOG.info(f"Got {namespace_name} request to delete all pages")

        with namespace_lock:
            namespace = self.loaded_namespaces.get(namespace_name)
            if namespace:
                to_rm = [p.name for p in namespace.pages if p.name not in except_pages]
                self._remove_pages(namespace_name, to_rm)

    def handle_delete_page(self, message: Message):
        """
        Handles request to remove one or more pages from a namespace.
        @param message: the message requesting page removal
        """
        message_is_valid = _validate_page_message(message)
        if message_is_valid:
            namespace_name = message.data["__from"]
            pages_to_remove = message.data.get("page_names") or \
                              message.data.get("page")  # backwards compat
            LOG.debug(f"Got {namespace_name} request to delete: {pages_to_remove}")
            with namespace_lock:
                self._remove_pages(namespace_name, pages_to_remove)

    def _remove_pages(self, namespace_name: str, pages_to_remove: List[str]):
        """
        Removes one or more pages from a namespace. Pages are removed from the
        bottom of the stack.
        @param namespace_name: the affected namespace
        @param pages_to_remove: names of pages to delete
        """
        namespace = self.loaded_namespaces.get(namespace_name)
        if namespace is not None and namespace in self.active_namespaces:
            page_positions = []
            for index, page in enumerate(namespace.pages):
                if page.name in pages_to_remove:
                    page_positions.append(index)

            if page_positions:
                page_positions.sort(reverse=True)
                namespace.remove_pages(page_positions)

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

    def _legacy_show_page(self, message: Message) -> List[GuiPage]:
        """
        Backwards-compat method to handle messages without ui_directories and
        page_names.
        @param message: message requesting to display pages
        @return: list of GuiPage objects
        """
        pages_to_show = message.data["page"]
        LOG.info(f"Handling legacy page show request. pages={pages_to_show}")

        pages_to_load = list()
        persist, duration = self._parse_persistence(message.data["__idle"])
        for page in pages_to_show:
            name = page.split('/')[-1]
            # check if persistence is type of int or bool
            pages_to_load.append(GuiPage(page, name, persist, duration))
        return pages_to_load

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
        page_resource_dirs = message.data.get('ui_directories')
        persistence = message.data["__idle"]
        show_index = message.data.get("index", None)

        LOG.debug(f"Got {namespace_name} request to show: {page_ids_to_show} at index: {show_index}")

        if not page_resource_dirs and page_ids_to_show and \
                all((x.startswith("SYSTEM") for x in page_ids_to_show)):
            page_resource_dirs = {"all": self._system_res_dir}

        if not all((page_ids_to_show, page_resource_dirs)):
            LOG.warning(f"GUI resources have not yet been uploaded for namespace: {namespace_name}")
            pages = self._legacy_show_page(message)
        else:
            pages = list()
            persist, duration = self._parse_persistence(message.data["__idle"])
            for page in page_ids_to_show:
                url = None
                name = page
                if isfile(page):
                    LOG.warning(f"Expected resource name but got file: {url}")
                    name = page.split('/')[-1]
                    url = f"file://{page}"
                elif "://" in page:
                    LOG.warning(f"Expected resource name but got URI: {page}")
                    name = page.split('/')[-1]
                    url = page
                pages.append(GuiPage(url, name, persist, duration,
                                     page, namespace_name, page_resource_dirs))

        if not pages:
            LOG.error(f"Activated namespace '{namespace_name}' has no pages! "
                      f"Did you provide 'ui_directories' ?")
            LOG.error(f"Can't show page, bad message: {message.data}")
            return

        with namespace_lock:
            if not self.active_namespaces:
                self._activate_namespace(namespace_name)
            else:
                active_namespace = self.active_namespaces[0]
                if active_namespace.skill_id != namespace_name:
                    self._activate_namespace(namespace_name)
            self._load_pages(pages, show_index)
            self._update_namespace_persistence(persistence)

    def _activate_namespace(self, namespace_name: str):
        """
        Instructs the GUI to load a namespace and its associated data.

        @param namespace_name: the name of the namespace to load
        """
        namespace = self._ensure_namespace_exists(namespace_name)

        if namespace in self.active_namespaces:
            namespace_position = self.active_namespaces.index(namespace)
            namespace.activate(namespace_position)
            if namespace_position != 0:
                LOG.info(f"Activating namespace: {namespace_name}")
                self.active_namespaces.insert(
                    0, self.active_namespaces.pop(namespace_position)
                )
        else:
            LOG.info(f"New namespace: {namespace_name}")
            namespace.add()
            self.active_namespaces.insert(0, namespace)
            # sync initial state
            for key, value in namespace.data.items():
                namespace.load_data(key, value)

        self._emit_namespace_displayed_event()

    def _ensure_namespace_exists(self, namespace_name: str) -> Namespace:
        """
        Retrieves the requested namespace, creating one if it doesn't exist.
        @param namespace_name: the name of the namespace being retrieved
        @returns: requested namespace
        """
        # TODO: - Update sync to match.
        namespace = self.loaded_namespaces.get(namespace_name)
        if namespace is None:
            namespace = Namespace(namespace_name)
            self.loaded_namespaces[namespace_name] = namespace

        return namespace

    def _load_pages(self, pages_to_show: List[GuiPage], show_index: int):
        """
        Loads the requested pages in the namespace.
        @param pages_to_show: list of pages to be loaded
        @param show_index: index to load pages at
        """
        if not len(pages_to_show) or show_index >= len(pages_to_show):
            LOG.error(f"requested invalid page index: {show_index}, defaulting to last page")
            show_index = len(pages_to_show) - 1

        active_namespace = self.active_namespaces[0]
        oldp = [p.name for p in active_namespace.pages]
        active_namespace.load_pages(pages_to_show, show_index)
        # LOG only on change
        if oldp != [p.name for p in active_namespace.pages]:
            pn = active_namespace.page_number
            LOG.info(f"Loaded {active_namespace.skill_id} at index: {pn} "
                     f"pages: {[p.name for p in active_namespace.pages]}")

    def _update_namespace_persistence(self, persistence: Union[bool, int]):
        """
        Sets the persistence of the namespace being activated.
        A namespace's persistence is the same as the persistence of the
        most recent pages added to a namespace.  For example, a multi-page
        namespace could show the first set of pages with a persistence of
        True (show until removed) and the last page with a persistence of
        15 seconds.  This would ensure that the namespace isn't removed while
        the skill is showing the pages.
        @param persistence: length of time the namespace should be displayed
        """
        for idx, namespace in enumerate(self.active_namespaces):
            if idx:
                if not namespace.persistent:
                    self._remove_namespace(namespace.skill_id)
            else:
                if namespace.persistent != persistence:
                    LOG.info(f"Setting namespace '{namespace.skill_id}' persistence to: {persistence}")
                    namespace.persistent = persistence

                if namespace.skill_id == self.idle_display_skill:
                    namespace.set_persistence(skill_type="idleDisplaySkill")
                else:
                    namespace.set_persistence(skill_type="genericSkill")
                    # check if there is a scheduled remove_namespace_timer
                    # and cancel it
                    if namespace.persistent and namespace.skill_id in \
                            self.remove_namespace_timers:
                        self.remove_namespace_timers[namespace.skill_id].cancel()
                        self._del_namespace_in_remove_timers(namespace.skill_id)

                if not namespace.persistent:
                    self._schedule_namespace_removal(namespace)

                self.active_namespaces[idx] = namespace

    def _schedule_namespace_removal(self, namespace: Namespace):
        """
        Uses a timer thread to remove the namespace.
        @param namespace: the namespace to be removed
        """
        # Before removing check if there isn't already a timer for this namespace
        if namespace.skill_id in self.remove_namespace_timers:
            return

        remove_namespace_timer = Timer(
            namespace.duration,
            self._remove_namespace_via_timer,
            args=(namespace.skill_id,)
        )
        LOG.info(f"Removal of namespace {namespace.skill_id} in "
                 f"{namespace.duration} seconds")
        remove_namespace_timer.start()
        self.remove_namespace_timers[namespace.skill_id] = remove_namespace_timer

    def _remove_namespace_via_timer(self, namespace_name: str):
        """
        Removes a namespace and the corresponding timer instance.
        @param namespace_name: name of namespace to remove
        """
        self._remove_namespace(namespace_name)
        self._del_namespace_in_remove_timers(namespace_name)

    def _remove_namespace(self, namespace_name: str):
        """
        Removes a namespace from the active namespace stack.
        @param namespace_name: name of namespace to remove
        """
        # Remove all timers associated with the namespace
        if namespace_name in self.remove_namespace_timers:
            self.remove_namespace_timers[namespace_name].cancel()
            self._del_namespace_in_remove_timers(namespace_name)

        namespace: Namespace = self.loaded_namespaces.get(namespace_name)
        if namespace is not None and namespace in self.active_namespaces:
            LOG.info(f"Removing namespace {namespace_name}")
            self.core_bus.emit(Message("gui.namespace.removed",
                                       data={"skill_id": namespace.skill_id}))
            namespace_position = self.active_namespaces.index(namespace)
            namespace.remove(namespace_position)
            self.active_namespaces.remove(namespace)

        self._emit_namespace_displayed_event()

    def _emit_namespace_displayed_event(self):
        """
        Emit a `gui.namespace.displayed` Message to notify core of changes.
        """
        if self.active_namespaces:
            displaying_namespace = self.active_namespaces[0]
            message_data = dict(skill_id=displaying_namespace.skill_id)
            # TODO - no known listeners ?
            self.core_bus.emit(
                Message("gui.namespace.displayed", data=message_data)
            )

    def handle_status_request(self, message: Message):
        """
        Handles a GUI status request by replying with the connection status.
        @param message: the request for status of the GUI
        """
        gui_connected = determine_if_gui_connected()
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
            with namespace_lock:
                self._update_namespace_data(namespace_name, message.data)

    def _update_namespace_data(self, namespace_name: str, data: dict):
        """
        Updates the values of namespace data attributes, unless unchanged.
        @param namespace_name: the name of the namespace to update
        @param data: the name and new value of one or more data attributes
        """
        namespace = self._ensure_namespace_exists(namespace_name)
        for key, value in data.items():
            if key not in RESERVED_KEYS and namespace.data.get(key) != value:
                namespace.data[key] = value
                if namespace in self.active_namespaces:
                    namespace.load_data(key, value)

    def handle_client_connected(self, message: Message):
        """
        Handles an event from the GUI indicating it is connected to the bus.
        @param message: the event sent by the GUI
        """
        # old style GUI has announced presence in core bus
        # send websocket port, the GUI should connect on it soon
        gui_id = message.data.get("gui_id")

        framework = message.data.get("framework")  # new api
        if framework is None:
            qt = message.data.get("qt_version", 5)  # mycroft-gui api
            if int(qt) == 6:
                framework = "qt6"
            else:
                framework = "qt5"

        LOG.info(f"GUI with ID {gui_id} connected to core message bus")
        websocket_config = get_gui_websocket_config()
        port = websocket_config["base_port"]
        message = message.forward("mycroft.gui.port",
                                  dict(port=port, gui_id=gui_id))
        self.core_bus.emit(message)

        if self.gui_file_path or self.gui_file_host_path:
            if not self._ready_event.wait(90):
                LOG.warning("Not reported ready after 90s")
            if framework not in self._connected_frameworks:
                LOG.debug(f"Requesting page upload for {framework}")
                self.core_bus.emit(Message("gui.request_page_upload",
                                           {'framework': framework},
                                           {"source": "gui",
                                            "destination": ["skills", "PHAL"]}))

        if framework not in self._connected_frameworks:
            LOG.debug(f"Connecting framework: {framework}")
            self._connected_frameworks.append(framework)

    def handle_page_interaction(self, message: Message):
        """
        Handles an event from the GUI indicating a page has been interacted with.
        @param message: the event sent by the GUI
        """
        # GUI has interacted with a page
        # Update and increase the namespace duration and reset the remove timer
        namespace_name = message.data.get("skill_id")
        pidx = message.data.get('page_number')
        LOG.info(f"GUI interacted with page in namespace {namespace_name}")
        namespace = self.loaded_namespaces.get(namespace_name)

        if namespace and pidx is not None and pidx != namespace.page_number:
            # update focused page
            namespace.page_gained_focus(pidx)

        # reschedule namespace timeout
        if namespace_name != self.idle_display_skill and \
                not namespace.persistent and \
                self.remove_namespace_timers[namespace.skill_id]:
            self.remove_namespace_timers[namespace.skill_id].cancel()
            self._del_namespace_in_remove_timers(namespace.skill_id)
            self._schedule_namespace_removal(namespace)

    def handle_page_gained_focus(self, message: Message):
        """
        Handles focus events from the GUI indicating the page has gained focus.
        @param message: the event sent by the GUI
        """
        namespace_name = message.data.get("skill_id")
        namespace_page_number = message.data.get("page_number")
        LOG.debug(f"Page in namespace {namespace_name} gained focus")
        namespace = self.loaded_namespaces.get(namespace_name)

        # first check if the namespace is already active
        if namespace in self.active_namespaces:
            # if the namespace is already active,
            # check if the page number has changed
            if namespace_page_number != namespace.page_number:
                namespace.page_gained_focus(namespace_page_number)

    def handle_namespace_global_back(self, message: Optional[Message]):
        """
        Handles global back events from the GUI.
        @param message: the event sent by the GUI
        """
        namespace_name = self.active_namespaces[0].skill_id
        namespace = self.loaded_namespaces.get(namespace_name)
        if namespace in self.active_namespaces:
            # prev page
            if namespace.page_number > 0:
                namespace.global_back()
            # homescreen
            else:
                self.core_bus.emit(Message("homescreen.manager.show_active"))

    def _del_namespace_in_remove_timers(self, namespace_name: str):
        """
        Delete namespace from remove_namespace_timers dict.
        @param namespace_name: name of namespace to be deleted
        """
        if namespace_name in self.remove_namespace_timers:
            del self.remove_namespace_timers[namespace_name]

    def _upload_system_resources(self):
        """
        Copy system GUI resources to the served file path
        """
        output_path = join(self.gui_file_path, "system")
        if exists(output_path):
            LOG.info(f"Removing existing system resources before updating")
            shutil.rmtree(output_path)
        shutil.copytree(self._system_res_dir, output_path)
        LOG.debug(f"Copied system resources to {self.gui_file_path}")
