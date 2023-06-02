from ovos_bus_client import Message
from ovos_config.config import Configuration
from ovos_utils.log import LOG
from ovos_plugin_manager.gui import OVOSGuiFactory
from ovos_gui.homescreen import HomescreenManager


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
        LOG.debug(f"Extensions Manager: Initializing {self.name} "
                  f"with active extension {self.active_extension}")
        self.activate_extension(self.active_extension.lower())

    def activate_extension(self, extension_id):
        mappings = {
            "smartspeaker": "ovos-gui-plugin-shell-companion",
            "bigscreen": "ovos-gui-plugin-bigscreen",
            "mobile": "ovos-gui-plugin-mobile",
            "plasmoid": "ovos-gui-plugin-plasmoid"
        }
        if extension_id.lower() in mappings:
            extension_id = mappings[extension_id.lower()]

        cfg = Configuration().get("gui", {})
        cfg["extension"] = extension_id
        LOG.info(f"Extensions Manager: Activating Extension {extension_id}")
        try:
            self.extension = OVOSGuiFactory.create(cfg, bus=self.bus,
                                                   gui=self.gui)
        except:
            if extension_id == "generic":
                raise
            LOG.exception(f"failed to load {extension_id}, "
                          f"falling back to 'generic'")
            cfg["extension"] = "generic"
            self.extension = OVOSGuiFactory.create(cfg, bus=self.bus,
                                                   gui=self.gui)
        self.extension.bind_homescreen()

        LOG.info(f"Extensions Manager: Activated Extension {extension_id}")
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


