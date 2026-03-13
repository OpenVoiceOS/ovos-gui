from ovos_bus_client import MessageBusClient, Message
from ovos_config.config import Configuration
from ovos_gui.namespace import NamespaceManager
from ovos_plugin_manager.gui import OVOSGuiFactory
from ovos_utils.log import LOG
from ovos_utils.process_utils import ProcessStatus, StatusCallbackMap, ProcessState


def on_started():
    LOG.info('Gui Service is starting up.')


def on_alive():
    LOG.info('Gui Service is alive.')


def on_ready():
    LOG.info('Gui Service is ready.')


def on_error(e='Unknown'):
    LOG.info(f'Gui Service failed to launch ({e})')


def on_stopping():
    LOG.info('Gui Service is shutting down...')


class GUIService:
    def __init__(self, alive_hook=on_alive, started_hook=on_started,
                 ready_hook=on_ready, error_hook=on_error,
                 stopping_hook=on_stopping):
        self.bus = MessageBusClient()
        self.extension_manager = None
        self.namespace_manager = None
        callbacks = StatusCallbackMap(on_started=started_hook,
                                      on_alive=alive_hook,
                                      on_ready=ready_hook,
                                      on_error=error_hook,
                                      on_stopping=stopping_hook)
        self.status = ProcessStatus('gui_service', callback_map=callbacks)
        self.status.bind(self.bus)

    def _init_bus_client(self):
        """
        Start the bus client daemon and wait for connection.
        """
        # Wait for connection
        Configuration.set_config_update_handlers(self.bus)
        if not self.bus.connected_event.is_set():
            self.bus.run_in_thread()
        self.bus.connected_event.wait()
        LOG.info('Connected to messagebus')

    def _load_adapter_plugins(self):
        """Load all installed ``opm.gui_adapter`` plugins and return instances."""
        adapter_config = Configuration().get("gui", {}).get("adapters", {})
        # Use create_all if available, otherwise fall back to empty list
        if hasattr(OVOSGuiFactory, 'create_all'):
            adapters = OVOSGuiFactory.create_all(config=adapter_config, bus=self.bus)
        else:
            adapters = []
        if not adapters:
            raise RuntimeError("No GUI adapters found. Configure at least one adapter in the 'gui.adapters' section of mycroft.conf")
        LOG.info(f"Loaded {len(adapters)} GUI adapter plugin(s)")
        return adapters

    def run(self):
        """
        Start the GUI after it has been constructed.
        """
        # Allow exceptions to be raised to the GUI Service
        # if they may cause the Service to fail.
        self.status.set_alive()
        self._init_bus_client()
        adapters = self._load_adapter_plugins()
        self.namespace_manager = NamespaceManager(self.bus, adapters=adapters)
        self.status.set_ready()
        LOG.info(f"GUI Service Ready")

    def is_alive(self) -> bool:
        """
        Respond to is_alive status request.
        """
        return self.status.state >= ProcessState.ALIVE

    def stop(self):
        """
        Perform any GUI shutdown processes.
        """
        self.status.set_stopping()
