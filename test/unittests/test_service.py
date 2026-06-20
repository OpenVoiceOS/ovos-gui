import unittest
from unittest import mock
from ovos_bus_client import MessageBusClient
from ovos_gui.service import (
    GUIService, on_started, on_alive, on_ready, on_error, on_stopping
)


class TestServiceCallbacks(unittest.TestCase):
    """Test module-level callback functions."""

    def test_on_started(self):
        """Test on_started callback."""
        on_started()

    def test_on_alive(self):
        """Test on_alive callback."""
        on_alive()

    def test_on_ready(self):
        """Test on_ready callback."""
        on_ready()

    def test_on_error_default(self):
        """Test on_error callback with default."""
        on_error()

    def test_on_error_with_message(self):
        """Test on_error callback with error message."""
        on_error("Test error")

    def test_on_stopping(self):
        """Test on_stopping callback."""
        on_stopping()


class TestGuiService(unittest.TestCase):
    """Test GUIService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_bus = mock.MagicMock(spec=MessageBusClient)
        self.mock_bus.connected_event = mock.MagicMock()
        self.mock_bus.connected_event.is_set = mock.MagicMock(return_value=True)
        self.mock_bus.connected_event.wait = mock.MagicMock()

    def test_init_default(self):
        """Test GUIService initialization with defaults."""
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus):
            service = GUIService()

            self.assertIsNotNone(service.bus)
            self.assertIsNone(service.namespace_manager)
            self.assertIsNotNone(service.status)

    def test_init_with_callbacks(self):
        """Test GUIService initialization with custom callbacks."""
        custom_callbacks = {
            'alive_hook': mock.Mock(),
            'started_hook': mock.Mock(),
            'ready_hook': mock.Mock(),
            'error_hook': mock.Mock(),
            'stopping_hook': mock.Mock(),
        }

        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus):
            service = GUIService(**custom_callbacks)
            self.assertIsNotNone(service.status)

    def test_is_alive_returns_boolean(self):
        """Test is_alive method returns boolean."""
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus):
            service = GUIService()
            result = service.is_alive()
            self.assertIsInstance(result, bool)

    def test_load_adapter_plugins_returns_list(self):
        """Test adapter plugin loading returns a list via the real factory.

        Regression for B1: the loader calls the published
        ``OVOSGUIAdapterFactory.create_all`` (no hasattr fallback).
        """
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus):
            service = GUIService()
            result = service._load_adapter_plugins()
            self.assertIsInstance(result, list)

    def test_load_adapter_plugins_headless_does_not_raise(self):
        """Regression for B1: zero installed adapters must NOT raise.

        A headless device degrades to no-op dispatch (empty adapter list)
        instead of raising RuntimeError.
        """
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus), \
             mock.patch('ovos_gui.service.OVOSGUIAdapterFactory.create_all',
                        return_value=[]) as mock_create_all:
            service = GUIService()
            result = service._load_adapter_plugins()  # must not raise
            self.assertEqual(result, [])
            mock_create_all.assert_called_once()

    def test_load_adapter_plugins_uses_real_factory(self):
        """The loader calls OVOSGUIAdapterFactory.create_all with bus + config."""
        fake_adapter = mock.Mock()
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus), \
             mock.patch('ovos_gui.service.OVOSGUIAdapterFactory.create_all',
                        return_value=[fake_adapter]) as mock_create_all:
            service = GUIService()
            result = service._load_adapter_plugins()
            self.assertEqual(result, [fake_adapter])
            mock_create_all.assert_called_once()
            # bus is forwarded so adapters can emit interaction events
            self.assertIn("bus", mock_create_all.call_args.kwargs)

    def test_init_bus_client_connected(self):
        """Test _init_bus_client when already connected."""
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus):
            self.mock_bus.connected_event.is_set.return_value = True

            service = GUIService()
            service._init_bus_client()

            # Should not call run_in_thread if already connected
            self.mock_bus.run_in_thread.assert_not_called()

    def test_init_bus_client_not_connected(self):
        """Test _init_bus_client when needs to connect."""
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus):
            self.mock_bus.connected_event.is_set.return_value = False

            service = GUIService()
            service._init_bus_client()

            # Should call run_in_thread if not connected
            self.mock_bus.run_in_thread.assert_called_once()
            # Should wait for connection
            self.mock_bus.connected_event.wait.assert_called_once()

    def test_stop(self):
        """Test stop method."""
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus):
            service = GUIService()
            # Should not raise
            service.stop()

    def test_run(self):
        """Test run method initialization sequence."""
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus), \
             mock.patch('ovos_gui.service.NamespaceManager') as mock_ns_mgr_class:

            mock_ns_mgr = mock.MagicMock()
            mock_ns_mgr_class.return_value = mock_ns_mgr

            service = GUIService()
            service.status = mock.MagicMock()
            service.run()

            # Verify status methods were called in sequence
            service.status.set_alive.assert_called_once()
            service.status.set_ready.assert_called_once()
            # Verify namespace manager was created
            mock_ns_mgr_class.assert_called_once()

    def test_run_full_flow(self):
        """Test run method full flow with real status object."""
        with mock.patch('ovos_gui.service.MessageBusClient', return_value=self.mock_bus), \
             mock.patch('ovos_gui.service.NamespaceManager'):
            service = GUIService()
            service.run()

            # Verify service initialized properly
            self.assertIsNotNone(service.namespace_manager)
