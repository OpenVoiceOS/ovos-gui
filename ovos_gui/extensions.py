from ovos_bus_client import Message
from ovos_config.config import Configuration
from ovos_utils.log import LOG

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

        LOG.info(f"Extensions Manager: Initializing {self.name} with active extension {self.active_extension}")
        self.activate_extension(self.active_extension.lower())

    def activate_extension(self, extension_id):
        # ToDo: use OPM factory class to load configured extension
        supported_extensions = ["smartspeaker", "bigscreen", "generic", "mobile", "plasmoid"]

        if extension_id.lower() not in supported_extensions:
            extension_id = "generic"

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


