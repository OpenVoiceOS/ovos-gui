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
"""GUI message bus implementation

The basic mechanism is:
    1) GUI client connects to the core messagebus
    2) Core prepares a port for a socket connection to this GUI
    3) The availability of the port is sent over the Core
    4) The GUI connects to the GUI message bus websocket
    5) Connection persists for graphical interaction indefinitely

If the connection is lost, it must be renegotiated and restarted.
"""
import asyncio
import json
from threading import Lock
from typing import List

from ovos_bus_client import Message, GUIMessage
from ovos_config.config import Configuration
from ovos_gui.page import GuiPage
from ovos_utils import create_daemon
from ovos_utils.log import LOG
from tornado import ioloop
from tornado.options import parse_command_line
from tornado.web import Application
from tornado.websocket import WebSocketHandler
# from ovos_gui.namespace import NamespaceManager

_write_lock = Lock()


def get_gui_websocket_config() -> dict:
    """
    Retrieves the configuration values for establishing a GUI message bus
    """
    config = Configuration()
    websocket_config = config["gui_websocket"]

    return websocket_config


def create_gui_service(nsmanager=None) -> Application:
    """
    Initiate a websocket for communicating with the GUI service.
    @param nsmanager: NamespaceManager instance
    """
    LOG.info('Starting message bus for GUI...')
    websocket_config = get_gui_websocket_config()
    # Disable all tornado logging so mycroft loglevel isn't overridden
    parse_command_line(['--logging=None'])

    routes = [(websocket_config['route'], GUIWebsocketHandler)]
    application = Application(routes, namespace_manager=nsmanager)
    application.listen(
        websocket_config['base_port'], websocket_config['host']
    )

    create_daemon(ioloop.IOLoop.instance().start)
    LOG.info('GUI Message bus started!')
    return application


def send_message_to_gui(message: dict):
    """
    Sends the supplied message to all connected GUI clients. This function does
    NOT account for the GUI framework in use by each client
    @param message: dict data to send to GUI clients
    """
    for connection in GUIWebsocketHandler.clients:
        try:
            connection.send(message)
        except Exception as e:
            LOG.exception(repr(e))


def determine_if_gui_connected() -> bool:
    """
    Returns True if any clients are connected to the GUI bus.
    """
    return len(GUIWebsocketHandler.clients) > 0


class GUIWebsocketHandler(WebSocketHandler):
    """Defines the websocket pipeline between the GUI and Mycroft."""
    clients = []

    def __init__(self, *args, **kwargs):
        WebSocketHandler.__init__(self, *args, **kwargs)
        self._framework = "qt5"
        self.ns_manager = self.application.settings.get("namespace_manager")

    @property
    def framework(self) -> str:
        """
        Get the GUI framework used by this client
        """
        return self._framework or "qt5"

    def open(self):
        """
        Add a new connection to `clients` and synchronize
        """
        GUIWebsocketHandler.clients.append(self)
        LOG.info('New Connection opened!')
        self.synchronize()

    def on_close(self):
        """
        Remove a closed connection from `clients`
        """
        LOG.info('Closing {}'.format(id(self)))
        GUIWebsocketHandler.clients.remove(self)

    def synchronize(self):
        """
        Upload namespaces, pages and data to the last connected client.
        """
        namespace_pos = 0

        for namespace in self.ns_manager.active_namespaces:
            LOG.info(f'Sync {namespace.skill_id}')
            # Insert namespace
            self.send({"type": "mycroft.session.list.insert",
                       "namespace": "mycroft.system.active_skills",
                       "position": namespace_pos,
                       "data": [{"skill_id": namespace.skill_id}]
                       })
            # Insert pages
            # if uri (path) can not be resolved, it might exist client side
            # if path doesn't exist in client side, client is responsible for resolving page by namespace/name
            self.send({"type": "mycroft.gui.list.insert",
                       "namespace": namespace.skill_id,
                       "position": 0,
                       "data": [{"url": page.get_uri(self.framework), "page": page.name}
                                for page in namespace.pages]
                       })
            # Insert data
            for key, value in namespace.data.items():
                self.send({"type": "mycroft.session.set",
                           "namespace": namespace.skill_id,
                           "data": {key: value}
                           })
            namespace_pos += 1

    def on_message(self, message: str):
        """
        Handle a message on the GUI websocket. Deserialize the message, map
        message types to valid equivalents for the core messagebus and emit
        on the core messagebus.
        @param message: Serialized Message
        """
        LOG.debug(f"Received: {message}")
        parsed_message = GUIMessage.deserialize(message)
        LOG.debug(f"Received: {parsed_message.msg_type}|{parsed_message.data}")

        # msg = json.loads(message)
        if parsed_message.msg_type == "mycroft.events.triggered" and \
                (parsed_message.data.get('event_name') == 'page_gained_focus' or
                 parsed_message.data.get('event_name') ==
                 'system.gui.user.interaction'):
            # System event, a page was changed
            event_name = parsed_message.data.get('event_name')
            if event_name == 'page_gained_focus':
                msg_type = 'gui.page_gained_focus'
            else:
                msg_type = 'gui.page_interaction'

            msg_data = \
                {'namespace': parsed_message.data['namespace'],
                 'page_number': parsed_message.data['parameters'].get('number'),
                 'skill_id': parsed_message.data['parameters'].get('skillId')}
        elif parsed_message.msg_type == "mycroft.events.triggered":
            # A normal event was triggered
            msg_type = f"{parsed_message.data['namespace']}." \
                       f"{parsed_message.data['event_name']}"
            msg_data = parsed_message.data['parameters']

        elif parsed_message.msg_type == 'mycroft.session.set':
            # A value was changed send it back to the skill
            msg_type = f"{parsed_message.data['namespace']}.set"
            msg_data = parsed_message.data['data']
        elif parsed_message.msg_type == 'mycroft.gui.connected':
            # new client connected to GUI

            # NOTE: mycroft-gui clients do this directly in core bus, don't
            # send it to gui bus. In those cases, framework is read from config,
            # defaulting to qt5 for backwards-compat.
            default_qt_version = \
                Configuration().get('gui', {}).get('default_qt_version') or 5
            msg_type = parsed_message.msg_type
            msg_data = parsed_message.data

            framework = msg_data.get("framework")  # new api
            if framework is None:
                # mycroft-gui api
                qt = msg_data.get("qt_version") or default_qt_version
                if int(qt) == 6:
                    framework = "qt6"
                else:
                    framework = "qt5"

            self._framework = framework
        else:
            # message not in spec
            # https://github.com/MycroftAI/mycroft-gui/blob/master/transportProtocol.md
            LOG.error(f"unknown GUI protocol message type, ignoring: "
                      f"{parsed_message.msg_type}")
            return

        parsed_message.context["gui_framework"] = self.framework
        message = Message(msg_type, msg_data, parsed_message.context)
        LOG.debug('Forwarding to core bus...')
        self.ns_manager.core_bus.emit(message)
        LOG.debug('Done!')

    def write_message(self, *arg, **kwarg):
        """
        Wraps WebSocketHandler.write_message() with a lock.
        """
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with _write_lock:
            super().write_message(*arg, **kwarg)

    def send_gui_pages(self, pages: List[GuiPage], namespace: str,
                       position: int):
        """
        Send GUI pages to this client, accounting for the client-specific pages
        @param pages: list of GuiPage objects to send
        @param namespace: namespace to put GuiPages in
        @param position: position to insert pages at
        """
        framework = self.framework
        # if uri (path) can not be resolved, it might exist client side
        # if path doesn't exist in client side, client is responsible for resolving page by namespace/name
        message = {
            "type": "mycroft.gui.list.insert",
            "namespace": namespace,
            "position": position,
            "data": [{"url": page.get_uri(framework), "page": page.name}
                     for page in pages]
        }
        LOG.debug(f"Showing pages: {message['data']}")
        self.send(message)

    def send(self, data: dict):
        """
        Send the given data across the socket as JSON
        @param data: Data to send to the GUI
        """
        s = json.dumps(data)
        self.write_message(s)

    def check_origin(self, origin):
        """
        Override origin check to make js connections work.
        """
        return True
