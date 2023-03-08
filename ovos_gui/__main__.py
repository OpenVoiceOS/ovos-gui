from ovos_config.locale import setup_locale
from ovos_utils import wait_for_exit_signal
from ovos_utils.log import LOG, init_service_logger
from ovos_utils.process_utils import reset_sigint_handler, PIDLock

from ovos_gui.service import GUIService


def on_ready():
    LOG.info("GUI websocket started!")


def on_stopping():
    LOG.info('GUI websocket is shutting down...')


def on_error(e='Unknown'):
    LOG.error(f'GUI websocket failed: {repr(e)}')


def main(ready_hook=on_ready, error_hook=on_error, stopping_hook=on_stopping):
    PIDLock.init()
    reset_sigint_handler()
    init_service_logger("gui")
    PIDLock("gui")
    LOG.debug("GUI websocket created")
    try:
        setup_locale()
        service = GUIService()
        service.run()
        ready_hook()
        wait_for_exit_signal()
        service.stop()
        stopping_hook()
    except Exception as e:
        error_hook(e)


if __name__ == "__main__":
    main()
