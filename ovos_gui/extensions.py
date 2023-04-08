import threading

from ovos_bus_client import Message
from ovos_backend_client.pairing import is_paired
from ovos_config.config import Configuration
from ovos_utils.log import LOG

from ovos_gui.homescreen import HomescreenManager
from ovos_gui.interfaces.mobile import MobileExtensionGuiInterface
from ovos_gui.interfaces.smartspeaker import SmartSpeakerExtensionGuiInterface


class ExtensionsManager:
    def __init__(self, name, bus, gui):
        """ Constructor for the Extension Manager. The Extension Manager is responsible for
        managing the extensions that define additional GUI behaviours for specific platforms.

        Args:
            name: Name of the extension manager
            bus: MessageBus instance
            gui: GUI instance
        """

        self.name = name
        self.bus = bus
        self.gui = gui
        core_config = Configuration()
        enclosure_config = core_config.get("gui") or {}
        self.active_extension = enclosure_config.get("extension", "generic")

        # ToDo: Add Exclusive Support For "Desktop", "Mobile" Extensions
        self.supported_extensions = ["smartspeaker", "bigscreen", "generic", "mobile", "plasmoid"]

        if self.active_extension.lower() not in self.supported_extensions:
            self.active_extension = "generic"

        LOG.info(
            f"Extensions Manager: Initializing {self.name} with active extension {self.active_extension}")
        self.activate_extension(self.active_extension.lower())

    def activate_extension(self, extension_id):
        LOG.info(f"Extensions Manager: Activating Extension {extension_id}")

        # map extension_id to class
        if extension_id == "smartspeaker":
            self.extension = SmartSpeakerExtension(self.bus, self.gui)
        elif extension_id == "bigscreen":
            self.extension = BigscreenExtension(self.bus, self.gui)
        elif extension_id == "mobile":
            self.extension = MobileExtension(self.bus, self.gui)
        elif extension_id == "plasmoid":
            self.extension = PlasmoidExtension(self.bus, self.gui)
        else:
            self.extension = GenericExtension(self.bus, self.gui)

        LOG.info(f"Extensions Manager: Activated Extension {extension_id}")
        self.bus.emit(
            Message("extension.manager.activated", {"id": extension_id}))

        def signal_available(message=None):
            message = message or Message("")
            self.bus.emit(message.forward("mycroft.gui.available",
                                          {"permanent": self.extension.permanent}))

        if self.extension.preload_gui:
            signal_available()
        else:
            self.bus.on("mycroft.gui.connected", signal_available)


class SmartSpeakerExtension:
    """ Smart Speaker Extension: This extension is responsible for managing the Smart Speaker
    specific GUI behaviours. This extension adds support for Homescreens and Homescreen Mangement.

    Args:
        bus: MessageBus instance
        gui: GUI instance
        preload_gui (bool): load GUI skills even if gui client not connected
        permanent (bool): disable unloading of GUI skills on gui client disconnections
    """

    def __init__(self, bus, gui, preload_gui=False, permanent=True):
        LOG.info("SmartSpeaker: Initializing")

        self.bus = bus
        self.gui = gui
        self.preload_gui = preload_gui
        self.permanent = permanent
        self.homescreen_manager = HomescreenManager(self.bus, self.gui)

        self.homescreen_thread = threading.Thread(
            target=self.homescreen_manager.run)
        self.homescreen_thread.start()

        self.device_paired = is_paired()
        self.backend = "unknown"
        self.gui_interface = SmartSpeakerExtensionGuiInterface(
            self.bus, self.homescreen_manager)

        try:
            self.bus.on("ovos.pairing.process.completed",
                        self.start_homescreen_process)
            self.bus.on("ovos.pairing.set.backend", self.set_backend_type)
            self.bus.on("mycroft.gui.screen.close",
                        self.handle_remove_namespace)
            self.bus.on("system.display.homescreen",
                        self.handle_system_display_homescreen)

        except Exception as e:
            LOG.error(f"SmartSpeaker: Init Bus Exception: {e}")

    def set_backend_type(self, message):
        backend = message.data.get("backend", "unknown")
        if not backend == "unknown":
            self.backend = backend
        else:
            backend = self._detect_backend()
            self.backend = backend

    def start_homescreen_process(self, message):
        self.device_paired = is_paired()
        if not self.backend == "local":
            self.homescreen_manager.show_homescreen()
            self.bus.emit(Message("ovos.shell.status.ok"))
        else:
            self.bus.emit(Message("ovos.shell.status.ok"))

    def _detect_backend(self):
        config = Configuration()
        server_config = config.get("server") or {}
        backend_config = server_config.get("url", "")
        if "https://api.mycroft.ai" in backend_config:
            return "remote"
        else:
            return "local"

    def handle_remove_namespace(self, message):
        LOG.info("Got Clear Namespace Event In Skill")
        get_skill_namespace = message.data.get("skill_id", "")
        if get_skill_namespace:
            self.bus.emit(Message("gui.clear.namespace",
                                  {"__from": get_skill_namespace}))

    def handle_system_display_homescreen(self, message):
        self.homescreen_manager.show_homescreen()


class BigscreenExtension:
    """ Bigscreen Platform Extension: This extension is responsible for managing the Bigscreen
    specific GUI behaviours. The bigscreen extension does not support Homescreens. It includes
    support for Window managment and Window behaviour.

    Args:
        bus: MessageBus instance
        gui: GUI instance
        preload_gui (bool): load GUI skills even if gui client not connected
        permanent (bool): disable unloading of GUI skills on gui client disconnections
    """

    def __init__(self, bus, gui, preload_gui=False, permanent=True):
        LOG.info("Bigscreen: Initializing")

        self.bus = bus
        self.gui = gui
        self.permanent = permanent
        self.preload_gui = preload_gui
        self.interaction_without_idle = True
        self.interaction_skill_id = None

        try:
            self.bus.on('mycroft.gui.screen.close', self.close_window_by_event)
            self.bus.on('mycroft.gui.force.screenclose',
                        self.close_window_by_force)
            self.bus.on('gui.page.show', self.on_gui_page_show)
            self.bus.on('gui.page_interaction', self.on_gui_page_interaction)
            self.bus.on('gui.namespace.removed', self.close_current_window)

        except Exception as e:
            LOG.error(f"Bigscreen: Init Bus Exception: {e}")

    def on_gui_page_show(self, message):
        override_idle = message.data.get('__idle')
        if override_idle is True:
            self.interaction_without_idle = True
        elif isinstance(override_idle, int) and not (override_idle, bool) and override_idle is not False:
            self.interaction_without_idle = True
        elif (message.data['page']):
            if not isinstance(override_idle, bool) or not isinstance(override_idle, int):
                self.interaction_without_idle = False

    def on_gui_page_interaction(self, message):
        skill_id = message.data.get('skill_id')
        self.interaction_skill_id = skill_id

    def handle_remove_namespace(self, message):
        get_skill_namespace = message.data.get("skill_id", "")
        LOG.info(f"Got Clear Namespace Event In Skill {get_skill_namespace}")
        if get_skill_namespace:
            self.bus.emit(Message("gui.clear.namespace",
                                  {"__from": get_skill_namespace}))

    def close_current_window(self, message):
        skill_id = message.data.get('skill_id')
        LOG.info(f"Bigscreen: Closing Current Window For Skill {skill_id}")
        self.bus.emit(Message('screen.close.idle.event',
                              data={"skill_idle_event_id": skill_id}))

    def close_window_by_event(self, message):
        self.interaction_without_idle = False
        self.bus.emit(Message('screen.close.idle.event',
                              data={"skill_idle_event_id": self.interaction_skill_id}))
        self.handle_remove_namespace(message)

    def close_window_by_force(self, message):
        skill_id = message.data.get('skill_id')
        self.bus.emit(Message('screen.close.idle.event',
                              data={"skill_idle_event_id": skill_id}))
        self.handle_remove_namespace(message)


class GenericExtension:
    """ Generic Platform Extension: This extension is responsible for managing the generic GUI behaviours
    for non specific platforms. The generic extension does optionally support Homescreen and Homescreen
    Management but it needs to be exclusively enabled in the configuration file.

    Args:
        bus: MessageBus instance
        gui: GUI instance
        preload_gui (bool): load GUI skills even if gui client not connected
        permanent (bool): disable unloading of GUI skills on gui client disconnections
    """

    def __init__(self, bus, gui, preload_gui=False, permanent=False):
        LOG.info("Generic: Initializing")

        self.bus = bus
        self.gui = gui
        self.preload_gui = preload_gui
        self.permanent = permanent
        core_config = Configuration()
        gui_config = core_config.get("gui") or {}
        generic_config = gui_config.get("generic", {})
        self.homescreen_supported = generic_config.get("homescreen_supported", False)

        if self.homescreen_supported:
            self.homescreen_manager = HomescreenManager(self.bus, self.gui)
            self.homescreen_thread = threading.Thread(
                target=self.homescreen_manager.run)
            self.homescreen_thread.start()

        try:
            self.bus.on("mycroft.gui.screen.close",
                        self.handle_remove_namespace)

        except Exception as e:
            LOG.error(f"Generic: Init Bus Exception: {e}")

    def handle_remove_namespace(self, message):
        LOG.info("Got Clear Namespace Event In Skill")
        get_skill_namespace = message.data.get("skill_id", "")
        if get_skill_namespace:
            self.bus.emit(Message("gui.clear.namespace",
                                  {"__from": get_skill_namespace}))


class MobileExtension:
    """ Mobile Platform Extension: This extension is responsible for managing the mobile GUI behaviours.
        This extension adds support for Homescreens and Homescreen Management and global page back navigation.

    Args:
        bus: MessageBus instance
        gui: GUI instance
        preload_gui (bool): load GUI skills even if gui client not connected
        permanent (bool): disable unloading of GUI skills on gui client disconnections
    """

    def __init__(self, bus, gui, preload_gui=True, permanent=True):
        LOG.info("Mobile: Initializing")

        self.bus = bus
        self.gui = gui
        self.preload_gui = preload_gui
        self.permanent = permanent
        self.homescreen_manager = HomescreenManager(self.bus, self.gui)

        self.homescreen_thread = threading.Thread(
            target=self.homescreen_manager.run)
        self.homescreen_thread.start()

        self.gui_interface = MobileExtensionGuiInterface(
            self.bus, self.homescreen_manager)

        self.bus.on('mycroft.gui.screen.close',
                    self.force_idle_screen)
        self.bus.on('mycroft.gui.forceHome',
                    self.force_home)
        self.bus.on('mycroft.gui.screen.request.page.back',
                    self.handle_page_back)

    def force_idle_screen(self, message):
        self.homescreen_manager.show_homescreen()

    def force_home(self, message):
        self.homescreen_manager.show_homescreen()

    def handle_page_back(self, message):
        self.gui.handle_namespace_global_back({})


class PlasmoidExtension:
    """ Plasmoid Platform Extension: This extension is responsible for managing the generic GUI behaviours
    for non specific platforms. The generic extension does optionally support Homescreen and Homescreen
    Management but it needs to be exclusively enabled in the configuration file.

    Args:
        bus: MessageBus instance
        gui: GUI instance
        preload_gui (bool): load GUI skills even if gui client not connected
        permanent (bool): disable unloading of GUI skills on gui client disconnections
    """

    def __init__(self, bus, gui, preload_gui=False, permanent=True):
        LOG.info("Plasmoid: Initializing")

        self.bus = bus
        self.gui = gui
        self.preload_gui = preload_gui
        self.permanent = permanent
        core_config = Configuration()
        gui_config = core_config.get("gui") or {}
        generic_config = gui_config.get("plasmoid", {})
        self.homescreen_supported = generic_config.get("homescreen_supported", False)

        if self.homescreen_supported:
            self.homescreen_manager = HomescreenManager(self.bus, self.gui)
            self.homescreen_thread = threading.Thread(
                target=self.homescreen_manager.run)
            self.homescreen_thread.start()

        try:
            self.bus.on("mycroft.gui.screen.close",
                        self.handle_remove_namespace)

        except Exception as e:
            LOG.error(f"Plasmoid: Init Bus Exception: {e}")

    def handle_remove_namespace(self, message):
        LOG.info("Got Clear Namespace Event In Skill")
        get_skill_namespace = message.data.get("skill_id", "")
        if get_skill_namespace:
            self.bus.emit(Message("gui.clear.namespace",
                                  {"__from": get_skill_namespace}))
