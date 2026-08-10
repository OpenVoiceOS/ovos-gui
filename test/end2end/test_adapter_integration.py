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
"""E2E integration tests for ovos-gui dispatch through real adapters.

Coverage:
- Skill -> NamespaceManager -> concrete adapter routing
- Real OVOSGUIAdapterFactory loading on a headless device (B1)
- session_id-only routing: default, a UUID, and two clients sharing one id
- Multi-adapter fan-out + per-adapter failure isolation
- The removed page-delete path no longer crashes (B4)
"""
import uuid

from ovos_bus_client.message import Message

from ovos_gui.namespace import NamespaceManager
from .conftest import RecordingGUIPlugin, ExplodingGUIPlugin


class TestFactoryLoading:
    """Regression for B1: the real factory loads cleanly when headless."""

    def test_factory_create_all_headless_returns_empty(self, fake_bus):
        from ovos_plugin_manager.gui import OVOSGUIAdapterFactory
        adapters = OVOSGUIAdapterFactory.create_all(bus=fake_bus, config={})
        assert isinstance(adapters, list)
        # no opm.gui_adapter plugins installed in the test env -> empty, no raise
        assert adapters == []

    def test_manager_runs_with_zero_adapters(self, fake_bus, message_factory):
        """A headless manager (no adapters) dispatches as a no-op, no crash."""
        manager = NamespaceManager(fake_bus, adapters=[])
        msg = message_factory["page_show"](["SYSTEM_text"], "test.skill")
        manager.handle_show_page(msg)  # must not raise
        assert manager.get_active_namespace("default").skill_id == "test.skill"


class TestDispatch:
    """Template + data dispatch to a concrete adapter."""

    def test_show_page_dispatches_template(self, manager, recording_adapter, message_factory):
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_weather"], "weather.skill"))
        weather = recording_adapter.calls_of("weather")
        assert len(weather) == 1
        # (kind, skill_id, data, session_id)
        assert weather[0][1] == "weather.skill"
        assert weather[0][3] == "default"

    def test_show_page_activates_namespace_on_adapter(self, manager, recording_adapter, message_factory):
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_text"], "text.skill"))
        activated = recording_adapter.calls_of("activated")
        assert ("activated", "text.skill", "default") in activated

    def test_set_value_forwards_session_update(self, manager, recording_adapter, message_factory):
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_weather"], "weather.skill"))
        manager.handle_set_value(
            message_factory["set_value"]("weather.skill", "temp", 22))

        updates = recording_adapter.calls_of("session_update")
        assert updates
        kind, skill_id, data, session_id = updates[-1]
        assert skill_id == "weather.skill"
        assert data == {"temp": 22}  # reserved keys stripped
        assert session_id == "default"

    def test_status_event_forwarded(self, manager, recording_adapter):
        manager.forward_to_gui(Message("recognizer_loop:wakeword", data={"x": 1}))
        status = recording_adapter.calls_of("status")
        assert status
        assert status[-1][1] == "recognizer_loop:wakeword"
        assert status[-1][3] == "default"

    def test_clear_namespace_deactivates_on_adapter(self, manager, recording_adapter, message_factory):
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_text"], "text.skill"))
        manager.handle_clear_namespace(
            message_factory["clear_namespace"]("text.skill"))

        deactivated = recording_adapter.calls_of("deactivated")
        assert ("deactivated", "text.skill", "default") in deactivated
        assert manager.get_active_namespace("default") is None


class TestSessionRouting:
    """session_id is the sole routing key (B6/B7/B8 collapse)."""

    def test_default_session_routing(self, manager, recording_adapter, message_factory):
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_text"], "test.skill", session_id="default"))
        assert recording_adapter.calls_of("text")[0][3] == "default"

    def test_uuid_session_routing(self, manager, recording_adapter, message_factory):
        sid = str(uuid.uuid4())
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_weather"], "weather.skill", session_id=sid))
        weather = recording_adapter.calls_of("weather")
        assert weather[0][3] == sid
        # the namespace lives under that exact session_id
        assert manager.get_active_namespace(sid).skill_id == "weather.skill"
        assert manager.get_active_namespace("default") is None

    def test_two_clients_sharing_session_get_same_dispatch(self, manager, recording_adapter, message_factory):
        """Two clients that share a session_id share one dispatch/state."""
        shared = "living-room"
        # client A shows weather
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_weather"], "weather.skill", session_id=shared))
        # client B (same session_id) pushes a data update
        manager.handle_set_value(
            message_factory["set_value"]("weather.skill", "temp", 19, session_id=shared))

        # exactly one session exists; both messages routed to it
        assert manager.get_all_sessions() == [shared]
        assert recording_adapter.calls_of("weather")[0][3] == shared
        assert recording_adapter.calls_of("session_update")[-1][3] == shared
        assert manager.get_namespace_data("weather.skill", shared)["temp"] == 19

    def test_distinct_sessions_isolated(self, manager, message_factory):
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_weather"], "weather.skill", session_id="kitchen"))
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_clock"], "clock.skill", session_id="bedroom"))

        assert manager.get_active_namespace("kitchen").skill_id == "weather.skill"
        assert manager.get_active_namespace("bedroom").skill_id == "clock.skill"


class TestMultiAdapter:
    """Fan-out to every adapter + failure isolation."""

    def test_fanout_to_all_adapters(self, fake_bus, recording_adapter, second_adapter, message_factory):
        manager = NamespaceManager(fake_bus, adapters=[recording_adapter, second_adapter])
        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_weather"], "weather.skill"))

        assert len(recording_adapter.calls_of("weather")) == 1
        assert len(second_adapter.calls_of("weather")) == 1

    def test_one_adapter_failure_does_not_block_others(self, fake_bus, message_factory):
        good = RecordingGUIPlugin()
        bad = ExplodingGUIPlugin()
        # bad adapter first: its raise must not stop the good adapter
        manager = NamespaceManager(fake_bus, adapters=[bad, good])

        manager.handle_show_page(
            message_factory["page_show"](["SYSTEM_weather"], "weather.skill"))

        # good adapter still received the template + activation
        assert len(good.calls_of("weather")) == 1
        assert good.calls_of("activated")
        # the namespace is still created (service did not crash)
        assert manager.get_active_namespace("default").skill_id == "weather.skill"


class TestRemovedPageDeletePath:
    """B4: page-delete handlers were removed; emitting them is a harmless no-op."""

    def test_page_delete_message_does_not_crash(self, manager):
        """No handler is registered for gui.page.delete; emitting it is inert."""
        bus = manager.core_bus
        # nothing is subscribed to these msg types -> emit is a no-op, no AttributeError
        bus.emit(Message("gui.page.delete", data={"__from": "x", "page_names": ["p"]}))
        bus.emit(Message("gui.page.delete.all", data={"__from": "x"}))
        # manager has no such handlers (dead page model removed)
        assert not hasattr(manager, "handle_delete_page")
        assert not hasattr(manager, "handle_delete_all_pages")
