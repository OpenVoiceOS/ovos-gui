import unittest
from unittest import mock


class TestMainCallbacks(unittest.TestCase):
    """Test __main__ module-level callback functions."""

    def test_on_ready(self):
        """Test on_ready callback logs message."""
        from ovos_gui.__main__ import on_ready
        with mock.patch('ovos_gui.__main__.LOG') as mock_log:
            on_ready()
            mock_log.info.assert_called_once()

    def test_on_stopping(self):
        """Test on_stopping callback logs message."""
        from ovos_gui.__main__ import on_stopping
        with mock.patch('ovos_gui.__main__.LOG') as mock_log:
            on_stopping()
            mock_log.info.assert_called_once()

    def test_on_error_default(self):
        """Test on_error callback with default parameter."""
        from ovos_gui.__main__ import on_error
        with mock.patch('ovos_gui.__main__.LOG') as mock_log:
            on_error()
            mock_log.error.assert_called_once()

    def test_on_error_with_exception(self):
        """Test on_error callback with exception."""
        from ovos_gui.__main__ import on_error
        error = RuntimeError("Test error")
        with mock.patch('ovos_gui.__main__.LOG') as mock_log:
            on_error(error)
            mock_log.error.assert_called_once()


class TestMain(unittest.TestCase):
    """Test __main__ main() function."""

    def test_main_default_callbacks(self):
        """Test main() with default callbacks."""
        from ovos_gui.__main__ import main
        with mock.patch('ovos_gui.__main__.init_service_logger'), \
             mock.patch('ovos_gui.__main__.setup_locale'), \
             mock.patch('ovos_gui.__main__.GUIService') as mock_gui_service, \
             mock.patch('ovos_gui.__main__.wait_for_exit_signal'), \
             mock.patch('ovos_gui.__main__.LOG'):
            mock_service_instance = mock.MagicMock()
            mock_gui_service.return_value = mock_service_instance

            main()

            mock_gui_service.assert_called_once()
            mock_service_instance.run.assert_called_once()
            mock_service_instance.stop.assert_called_once()

    def test_main_custom_callbacks(self):
        """Test main() with custom callbacks."""
        from ovos_gui.__main__ import main
        ready_hook = mock.Mock()
        error_hook = mock.Mock()
        stopping_hook = mock.Mock()

        with mock.patch('ovos_gui.__main__.init_service_logger'), \
             mock.patch('ovos_gui.__main__.setup_locale'), \
             mock.patch('ovos_gui.__main__.GUIService') as mock_gui_service, \
             mock.patch('ovos_gui.__main__.wait_for_exit_signal'), \
             mock.patch('ovos_gui.__main__.LOG'):
            mock_service_instance = mock.MagicMock()
            mock_gui_service.return_value = mock_service_instance

            main(ready_hook=ready_hook, error_hook=error_hook, stopping_hook=stopping_hook)

            ready_hook.assert_called_once()
            error_hook.assert_not_called()
            stopping_hook.assert_called_once()

    def test_main_exception_handling(self):
        """Test main() exception handling calls error_hook."""
        from ovos_gui.__main__ import main
        error_hook = mock.Mock()

        with mock.patch('ovos_gui.__main__.init_service_logger'), \
             mock.patch('ovos_gui.__main__.setup_locale'), \
             mock.patch('ovos_gui.__main__.GUIService') as mock_gui_service, \
             mock.patch('ovos_gui.__main__.LOG'):
            mock_service_instance = mock.MagicMock()
            mock_service_instance.run.side_effect = RuntimeError("Service error")
            mock_gui_service.return_value = mock_service_instance

            main(error_hook=error_hook)

            error_hook.assert_called_once()

    def test_main_initializes_logger(self):
        """Test main() initializes service logger."""
        from ovos_gui.__main__ import main
        with mock.patch('ovos_gui.__main__.init_service_logger') as mock_init_logger, \
             mock.patch('ovos_gui.__main__.setup_locale'), \
             mock.patch('ovos_gui.__main__.GUIService') as mock_gui_service, \
             mock.patch('ovos_gui.__main__.wait_for_exit_signal'), \
             mock.patch('ovos_gui.__main__.LOG'):
            mock_service_instance = mock.MagicMock()
            mock_gui_service.return_value = mock_service_instance

            main()

            mock_init_logger.assert_called_once_with("gui")

    def test_main_sets_up_locale(self):
        """Test main() sets up locale."""
        from ovos_gui.__main__ import main
        with mock.patch('ovos_gui.__main__.init_service_logger'), \
             mock.patch('ovos_gui.__main__.setup_locale') as mock_setup_locale, \
             mock.patch('ovos_gui.__main__.GUIService') as mock_gui_service, \
             mock.patch('ovos_gui.__main__.wait_for_exit_signal'), \
             mock.patch('ovos_gui.__main__.LOG'):
            mock_service_instance = mock.MagicMock()
            mock_gui_service.return_value = mock_service_instance

            main()

            mock_setup_locale.assert_called_once()

    def test_main_waits_for_exit_signal(self):
        """Test main() waits for exit signal."""
        from ovos_gui.__main__ import main
        with mock.patch('ovos_gui.__main__.init_service_logger'), \
             mock.patch('ovos_gui.__main__.setup_locale'), \
             mock.patch('ovos_gui.__main__.GUIService') as mock_gui_service, \
             mock.patch('ovos_gui.__main__.wait_for_exit_signal') as mock_wait, \
             mock.patch('ovos_gui.__main__.LOG'):
            mock_service_instance = mock.MagicMock()
            mock_gui_service.return_value = mock_service_instance

            main()

            mock_wait.assert_called_once()
