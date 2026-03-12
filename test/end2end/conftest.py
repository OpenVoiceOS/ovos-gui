# Copyright 2026 OpenVoiceOS Contributors
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
"""Pytest fixtures for E2E adapter integration tests."""
import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Optional

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus
from ovos_config.config import Configuration

from ovos_gui.namespace import NamespaceManager


@pytest.fixture
def fake_bus():
    """Fixture: FakeBus for testing without real MessageBus daemon."""
    return FakeBus()


@pytest.fixture
def mock_configuration():
    """Fixture: Mock configuration for GUI service."""
    config_mock = Mock(spec=Configuration)
    config_dict = {
        "extension": "generic",
        "idle_display_skill": None,
        "generic": {},
        "adapters": {},
        "gui_websocket": {
            "host": "0.0.0.0",
            "base_port": 18181,
            "route": "/gui",
            "ssl": False,
        }
    }
    config_mock.get.return_value = config_dict
    return config_mock


@pytest.fixture
def legacy_adapter():
    """Fixture: Mocked legacy (Qt) adapter instance.

    Creates a mock adapter that implements the AbstractGUIPlugin interface
    matching ovos-legacy-mycroft-gui-plugin structure.

    TECH-003: E2E tests verify NamespaceManager → Adapter message routing
    without loading heavy external dependencies.
    """
    adapter = Mock()

    # Implement all 21 template handler methods
    template_handlers = [
        "handle_show_weather",
        "handle_show_text",
        "handle_show_timer",
        "handle_show_list",
        "handle_show_image",
        "handle_show_animated_image",
        "handle_show_grid",
        "handle_show_table",
        "handle_show_html",
        "handle_show_url",
        "handle_show_media_player",
        "handle_show_clock",
        "handle_show_confirm",
        "handle_show_select",
        "handle_show_face",
        "handle_show_scroll",
        "handle_show_map",
        "handle_show_form",
        "handle_show_template",
        "handle_show_custom",
        "handle_page_interaction",
    ]

    for handler_name in template_handlers:
        setattr(adapter, handler_name, Mock(return_value=None))

    # Implement all lifecycle hooks
    adapter.on_namespace_activated = Mock(return_value=None)
    adapter.on_namespace_deactivated = Mock(return_value=None)
    adapter.on_session_data_changed = Mock(return_value=None)
    adapter.on_page_gained_focus = Mock(return_value=None)
    adapter.on_status_event = Mock(return_value=None)

    # Track all method calls for verification
    adapter._all_calls = []

    # Wrap all mocked methods to track calls
    for attr_name in dir(adapter):
        attr = getattr(adapter, attr_name)
        if isinstance(attr, Mock) and not attr_name.startswith("_"):
            def make_wrapper(method_name, original_mock):
                def wrapper(*args, **kwargs):
                    adapter._all_calls.append((method_name, args, kwargs))
                    return original_mock(*args, **kwargs)
                return wrapper

            wrapped_mock = Mock(side_effect=make_wrapper(attr_name, attr))
            setattr(adapter, attr_name, wrapped_mock)

    yield adapter


@pytest.fixture
def pyhtmx_adapter():
    """Fixture: Mocked PyHTMX (web) adapter instance.

    Creates a mock adapter that implements the AbstractGUIPlugin interface
    matching pyhtmx-gui-client structure.

    TECH-003: E2E tests verify multi-adapter routing without external deps.
    """
    adapter = Mock()

    # Implement all 21 template handler methods
    template_handlers = [
        "handle_show_weather",
        "handle_show_text",
        "handle_show_timer",
        "handle_show_list",
        "handle_show_image",
        "handle_show_animated_image",
        "handle_show_grid",
        "handle_show_table",
        "handle_show_html",
        "handle_show_url",
        "handle_show_media_player",
        "handle_show_clock",
        "handle_show_confirm",
        "handle_show_select",
        "handle_show_face",
        "handle_show_scroll",
        "handle_show_map",
        "handle_show_form",
        "handle_show_template",
        "handle_show_custom",
        "handle_page_interaction",
    ]

    for handler_name in template_handlers:
        setattr(adapter, handler_name, Mock(return_value=None))

    # Implement all lifecycle hooks
    adapter.on_namespace_activated = Mock(return_value=None)
    adapter.on_namespace_deactivated = Mock(return_value=None)
    adapter.on_session_data_changed = Mock(return_value=None)
    adapter.on_page_gained_focus = Mock(return_value=None)
    adapter.on_status_event = Mock(return_value=None)

    # Track all method calls for verification
    adapter._all_calls = []

    yield adapter


@pytest.fixture
def namespace_manager_with_adapters(fake_bus, legacy_adapter):
    """Fixture: NamespaceManager with real legacy adapter loaded.

    Creates a NamespaceManager instance and injects the real legacy adapter.
    """
    manager = NamespaceManager(fake_bus)

    # Inject real adapter
    manager.adapters = [legacy_adapter]

    # Track calls to adapters for verification
    manager._adapter_calls = []

    yield manager


@pytest.fixture
def message_factory():
    """Fixture: Factory for creating GUI bus messages."""
    def create_page_show_message(
        page_names: List[str],
        skill_id: str,
        data: Optional[dict] = None,
        routing_key: str = "default",
        session_id: str = "default",
        persistent: bool = False
    ) -> Message:
        """Create a gui.page.show message."""
        msg_data = {
            "page_names": page_names,
            "__from": skill_id,
            "__idle": persistent,  # Required field for persistence flag
            "index": 0,  # Show at index 0
        }
        if data:
            msg_data.update(data)

        context = {
            "source_site_id": routing_key,
            "session": {
                "session_id": session_id,
                "site_id": routing_key,
            }
        }
        return Message("gui.page.show", data=msg_data, context=context)

    def create_set_value_message(
        namespace: str,
        key: str,
        value,
        routing_key: str = "default",
        session_id: str = "default"
    ) -> Message:
        """Create a gui.value.set message."""
        msg_data = {
            "__from": namespace,  # Required field for namespace identification
            key: value,
        }
        context = {
            "source_site_id": routing_key,
            "session": {
                "session_id": session_id,
                "site_id": routing_key,
            }
        }
        return Message("gui.value.set", data=msg_data, context=context)

    def create_page_delete_message(
        namespace: str,
        page_names: List[str],
        routing_key: str = "default",
        session_id: str = "default"
    ) -> Message:
        """Create a gui.page.delete message."""
        msg_data = {
            "namespace": namespace,
            "page_names": page_names,
        }
        context = {
            "source_site_id": routing_key,
            "session": {
                "session_id": session_id,
                "site_id": routing_key,
            }
        }
        return Message("gui.page.delete", data=msg_data, context=context)

    return {
        "page_show": create_page_show_message,
        "set_value": create_set_value_message,
        "page_delete": create_page_delete_message,
    }


@pytest.fixture
def assert_adapter_called():
    """Fixture: Helper to assert adapter methods were called."""
    def _assert(
        adapter,
        method_name: str,
        expected_calls: Optional[int] = None,
        contains_data: Optional[dict] = None
    ):
        """Assert that adapter method was called.

        Args:
            adapter: The adapter instance
            method_name: Name of the method to check (e.g., "handle_show_weather")
            expected_calls: If specified, assert exact number of calls
            contains_data: If specified, assert call contained this data (substring match)
        """
        matching_calls = [
            call for call in adapter._mock_calls
            if call[0] == method_name
        ]

        assert len(matching_calls) > 0, (
            f"Adapter method {method_name} was never called. "
            f"Calls: {adapter._mock_calls}"
        )

        if expected_calls is not None:
            assert len(matching_calls) == expected_calls, (
                f"Expected {expected_calls} calls to {method_name}, "
                f"got {len(matching_calls)}"
            )

        if contains_data is not None:
            # Check if any call contains the expected data
            found = False
            for call in matching_calls:
                call_data = call[1]  # Second element is the data
                if isinstance(call_data, dict) and contains_data.items() <= call_data.items():
                    found = True
                    break

            assert found, (
                f"No call to {method_name} contained expected data {contains_data}. "
                f"Calls: {matching_calls}"
            )

    return _assert
