from ovos_bus_client import Message, MessageBusClient
from ovos_config.config import Configuration
from ovos_utils.log import LOG
from ovos_plugin_manager.gui import OVOSGuiFactory
from ovos_gui.homescreen import HomescreenManager


class ExtensionsManager:
    def __init__(self, name: str, bus: MessageBusClient):
        """
        Constructor for the Extension Manager. The Extension Manager is
        responsible for managing the extensions that define additional GUI
        behaviours for specific platforms.
        @param name: Name of the extension manager
        @param bus: MessageBus instance
        """

        self.name = name
        self.bus = bus
        self.homescreen_manager = HomescreenManager(self.bus)
        core_config = Configuration()
        enclosure_config = core_config.get("gui") or {}
        self.active_extension = enclosure_config.get("extension", "generic")
        LOG.debug(f"Extensions Manager: Initializing {self.name} "
                  f"with active extension {self.active_extension}")
        self.activate_extension(self.active_extension.lower())

    def activate_extension(self, extension_id: str):
        """
        Activate the requested extension
        @param extension_id: GUI Plugin entrypoint to activate
        """
        mappings = {
            "smartspeaker": "ovos-gui-plugin-shell-companion",
            "bigscreen": "ovos-gui-plugin-bigscreen",
            "mobile": "ovos-gui-plugin-mobile",
            "plasmoid": "ovos-gui-plugin-plasmoid"
        }
        if extension_id.lower() in mappings:
            extension_id = mappings[extension_id.lower()]

        cfg = dict(Configuration().get("gui", {}))
        cfg["module"] = extension_id
        # LOG.info(f"Extensions Manager: Activating Extension {extension_id}")
        try:
            LOG.info(f"Creating GUI with config={cfg}")
            self.extension = OVOSGuiFactory.create(cfg, bus=self.bus)
        except:
            if extension_id == "generic":
                raise
            LOG.exception(f"failed to load {extension_id}, "
                          f"falling back to 'generic'")
            cfg["module"] = "generic"
            self.extension = OVOSGuiFactory.create(cfg, bus=self.bus)

        self.extension.bind_homescreen(self.homescreen_manager)

        LOG.info(f"Extensions Manager - Activated: {extension_id} "
                 f"({self.extension.__class__.__name__})")
        self.bus.emit(
            Message("extension.manager.activated", {"id": extension_id}))

        def signal_available(message=None):
            message = message or Message("")
            self.bus.emit(
                message.forward("mycroft.gui.available",
                                {"permanent": self.extension.permanent}))

        if self.extension.preload_gui:
            signal_available()
        else:
            self.bus.on("mycroft.gui.connected", signal_available)


