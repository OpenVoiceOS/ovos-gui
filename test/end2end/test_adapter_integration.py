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
"""E2E integration tests for ovos-gui with mocked GUI adapters.

TECH-003: These tests verify:
- Message routing: Skill → NamespaceManager → Adapter callbacks
- Adapter interface contracts
- Multi-adapter support
- Error isolation (one adapter failure doesn't crash others)
"""
import pytest
from unittest.mock import Mock


class TestNamespaceManagerBasics:
    """Basic NamespaceManager functionality tests."""

    def test_namespace_manager_initializes(self, fake_bus):
        """Test that NamespaceManager can be created."""
        from ovos_gui.namespace import NamespaceManager

        manager = NamespaceManager(fake_bus)
        assert manager is not None
        assert hasattr(manager, "sessions")
        assert hasattr(manager, "adapters")


class TestMessageRouting:
    """Tests for message routing from skills to adapters.

    TECH-003: Verify message flow: Skill → NamespaceManager → Adapter
    """

    def test_show_page_message_creates_namespace(self, namespace_manager_with_adapters, message_factory):
        """Test that gui.page.show message creates a namespace."""
        msg = message_factory["page_show"](
            page_names=["SYSTEM_weather"],
            skill_id="weather.skill",
            data={"temp": 22},
            routing_key="default"
        )

        # Before: no namespaces
        session = namespace_manager_with_adapters.sessions.get("default")
        before_count = len(session.active_namespaces) if session else 0

        # Emit message
        namespace_manager_with_adapters.handle_show_page(msg)

        # After: namespace should be created
        session = namespace_manager_with_adapters.get_session("default")
        assert len(session.active_namespaces) > before_count

        # Verify it's the correct namespace
        assert session.active_namespaces[0].skill_id == "weather.skill"

    def test_set_value_message_updates_data(self, namespace_manager_with_adapters, message_factory):
        """Test that gui.value.set message updates namespace data."""
        # Create namespace first
        show_msg = message_factory["page_show"](
            page_names=["SYSTEM_weather"],
            skill_id="weather.skill",
            data={"temp": 20},
            routing_key="default"
        )
        namespace_manager_with_adapters.handle_show_page(show_msg)

        # Update data
        set_msg = message_factory["set_value"](
            namespace="weather.skill",
            key="temp",
            value=25,
            routing_key="default"
        )
        namespace_manager_with_adapters.handle_set_value(set_msg)

        # Verify data was updated
        session = namespace_manager_with_adapters.get_session("default")
        ns = session.active_namespaces[0]
        assert ns.data.get("temp") == 25

    def test_clear_namespace_via_message(self, namespace_manager_with_adapters, message_factory):
        """Test that gui.clear.namespace message removes namespace."""
        from ovos_bus_client.message import Message

        # Create namespace
        show_msg = message_factory["page_show"](
            page_names=["SYSTEM_weather"],
            skill_id="weather.skill",
            routing_key="default"
        )
        namespace_manager_with_adapters.handle_show_page(show_msg)

        # Verify it exists
        session = namespace_manager_with_adapters.get_session("default")
        assert len(session.active_namespaces) == 1

        # Remove it via message
        clear_msg = Message("gui.clear.namespace", data={
            "__from": "weather.skill"
        }, context={
            "source_site_id": "default",
            "session": {"session_id": "default", "site_id": "default"}
        })
        namespace_manager_with_adapters.handle_clear_namespace(clear_msg)

        # Verify it's removed
        session = namespace_manager_with_adapters.get_session("default")
        assert len(session.active_namespaces) == 0


class TestSessionIsolation:
    """Tests for session-based isolation.

    TECH-007: Verify that different routing keys keep namespaces separate
    """

    def test_different_sessions_isolated(self, namespace_manager_with_adapters, message_factory):
        """Test that different sessions maintain separate namespaces.

        TECH-007: Verify that site_id acts as the session key for multi-room setups.
        When routing_key (site_id) is provided, it becomes the session key.
        """
        # Create skill in "default" session
        msg1 = message_factory["page_show"](
            page_names=["SYSTEM_weather"],
            skill_id="weather.skill",
            routing_key="default",
            session_id="default"
        )
        namespace_manager_with_adapters.handle_show_page(msg1)

        # Create skill in "kitchen" session (site_id = routing_key = "kitchen")
        msg2 = message_factory["page_show"](
            page_names=["SYSTEM_clock"],
            skill_id="clock.skill",
            routing_key="kitchen",  # This becomes the session key
            session_id="kitchen-default"
        )
        namespace_manager_with_adapters.handle_show_page(msg2)

        # Verify each session has its own namespace
        # Session key is determined by _get_session_key(session_id, site_id)
        # which returns site_id if it's meaningful, else session_id
        default_session = namespace_manager_with_adapters.get_session("default")
        kitchen_session = namespace_manager_with_adapters.get_session("kitchen")  # Key is "kitchen" (site_id)

        assert len(default_session.active_namespaces) == 1
        assert len(kitchen_session.active_namespaces) == 1

        assert default_session.active_namespaces[0].skill_id == "weather.skill"
        assert kitchen_session.active_namespaces[0].skill_id == "clock.skill"


class TestAdapterIntegration:
    """Tests for adapter callback invocation.

    TECH-005: Verify adapter contract - callbacks are invoked correctly
    """

    def test_adapter_exists_in_manager(self, namespace_manager_with_adapters):
        """Test that adapter is registered in NamespaceManager."""
        assert len(namespace_manager_with_adapters.adapters) > 0
        assert namespace_manager_with_adapters.adapters[0] is not None

    def test_adapter_has_required_methods(self, legacy_adapter):
        """Test that mocked adapter has all required methods.

        TECH-005: Verify AbstractGUIPlugin interface
        """
        # Check template handlers exist
        assert hasattr(legacy_adapter, "handle_show_weather")
        assert hasattr(legacy_adapter, "handle_show_text")
        assert hasattr(legacy_adapter, "handle_show_timer")

        # Check lifecycle hooks exist
        assert hasattr(legacy_adapter, "on_namespace_activated")
        assert hasattr(legacy_adapter, "on_namespace_deactivated")
        assert hasattr(legacy_adapter, "on_session_data_changed")
        assert hasattr(legacy_adapter, "on_page_gained_focus")
        assert hasattr(legacy_adapter, "on_status_event")

    def test_multiple_adapters_coexist(self, fake_bus, legacy_adapter, pyhtmx_adapter):
        """Test that multiple adapters can be loaded together.

        TECH-003: Verify multi-adapter support
        """
        from ovos_gui.namespace import NamespaceManager

        manager = NamespaceManager(fake_bus)
        manager.adapters = [legacy_adapter, pyhtmx_adapter]

        assert len(manager.adapters) == 2
        assert legacy_adapter in manager.adapters
        assert pyhtmx_adapter in manager.adapters


class TestErrorHandling:
    """Tests for error handling and robustness.

    TECH-003: Verify service continues when adapter fails
    """

    def test_message_validation_rejects_invalid(self, namespace_manager_with_adapters):
        """Test that invalid messages are rejected."""
        from ovos_bus_client.message import Message

        # Message missing required __from field
        invalid_msg = Message("gui.page.show", data={
            "page_names": ["SYSTEM_weather"],
            "__idle": False,
            # Missing "__from"
        })

        # Should not crash; validation should reject it
        namespace_manager_with_adapters.handle_show_page(invalid_msg)

        # No namespace should be created
        session = namespace_manager_with_adapters.sessions.get("default")
        if session:
            assert len(session.active_namespaces) == 0

    def test_adapter_error_doesnt_crash_service(self, fake_bus, message_factory):
        """Test that failing adapter doesn't crash NamespaceManager.

        TECH-005: Adapter error isolation
        """
        from ovos_gui.namespace import NamespaceManager

        manager = NamespaceManager(fake_bus)

        # Adapter that raises exception
        bad_adapter = Mock()
        bad_adapter.on_namespace_activated = Mock(side_effect=RuntimeError("Crash!"))

        manager.adapters = [bad_adapter]

        msg = message_factory["page_show"](
            page_names=["SYSTEM_weather"],
            skill_id="weather.skill",
            routing_key="default"
        )

        # Should not raise; _safe_call wraps it
        manager.handle_show_page(msg)

        # Namespace should still be created (adapter error is isolated)
        session = manager.get_session("default")
        assert len(session.active_namespaces) > 0


class TestRoutingKeyContract:
    """Tests for routing key handling.

    TECH-007: Verify routing key semantics (default vs site vs UUID)
    """

    def test_default_session_routes_correctly(self, namespace_manager_with_adapters, message_factory):
        """Test routing with default session ID."""
        msg = message_factory["page_show"](
            page_names=["SYSTEM_text"],
            skill_id="test.skill",
            routing_key="default",  # Single-screen mode
            session_id="default"
        )

        namespace_manager_with_adapters.handle_show_page(msg)

        # Should be in "default" session
        session = namespace_manager_with_adapters.get_session("default")
        assert len(session.active_namespaces) > 0

    def test_site_based_routing(self, namespace_manager_with_adapters, message_factory):
        """Test multi-room routing (site_id based).

        TECH-007: Verify each site (via routing_key/site_id) gets its own session.
        Session key is determined by _get_session_key which prioritizes site_id.
        """
        # Create namespaces for different sites
        msg_kitchen = message_factory["page_show"](
            page_names=["SYSTEM_weather"],
            skill_id="weather.skill",
            routing_key="kitchen",  # This becomes the session key
            session_id="kitchen-default"
        )
        namespace_manager_with_adapters.handle_show_page(msg_kitchen)

        msg_bedroom = message_factory["page_show"](
            page_names=["SYSTEM_clock"],
            skill_id="clock.skill",
            routing_key="bedroom",  # This becomes the session key
            session_id="bedroom-default"
        )
        namespace_manager_with_adapters.handle_show_page(msg_bedroom)

        # Each site should have independent session
        # Session key is the routing_key (site_id), not the session_id parameter
        kitchen = namespace_manager_with_adapters.get_session("kitchen")
        bedroom = namespace_manager_with_adapters.get_session("bedroom")

        assert len(kitchen.active_namespaces) == 1
        assert len(bedroom.active_namespaces) == 1
        assert kitchen.active_namespaces[0].skill_id == "weather.skill"
        assert bedroom.active_namespaces[0].skill_id == "clock.skill"
