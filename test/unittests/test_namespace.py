# Copyright 2022 Mycroft AI Inc.
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
"""Tests for the GUI namespace helper classes (session_id-only routing)."""
from unittest import TestCase, mock
from unittest.mock import Mock

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

from ovos_gui.namespace import Namespace, NamespaceManager, _validate_page_message

PATCH_MODULE = "ovos_gui.namespace"


class TestNamespaceFunctions(TestCase):
    def test_validate_page_message(self):
        """Test _validate_page_message function."""
        valid_msg = Message("gui.page.show", data={
            "page_names": ["SYSTEM_weather"], "__from": "skill_id", "__idle": 30
        })
        self.assertTrue(_validate_page_message(valid_msg))

        # Invalid: missing page_names
        invalid1 = Message("gui.page.show", data={"__from": "skill_id", "__idle": 30})
        self.assertFalse(_validate_page_message(invalid1))

        # Invalid: missing __from
        invalid2 = Message("gui.page.show", data={"page_names": ["SYSTEM_weather"], "__idle": 30})
        self.assertFalse(_validate_page_message(invalid2))

        # Missing __idle is NOT a validation error (only page_names and __from)
        invalid3 = Message("gui.page.show", data={"page_names": ["SYSTEM_weather"], "__from": "skill_id"})
        self.assertTrue(_validate_page_message(invalid3))


class TestNamespace(TestCase):
    """Tests for Namespace class."""

    def setUp(self):
        self.namespace = Namespace("test_skill")

    def test_namespace_initialization(self):
        ns = Namespace("foo_skill")
        self.assertEqual(ns.skill_id, "foo_skill")
        self.assertFalse(ns.persistent)
        self.assertEqual(ns.duration, 30)
        self.assertEqual(ns.data, {})
        self.assertFalse(ns.session_set)

    def test_namespace_add(self):
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.add()

    def test_namespace_activate(self):
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.activate(position=0)

    def test_namespace_remove(self):
        self.namespace.data = {"key1": "value1", "key2": "value2"}
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.remove(position=0)
        self.assertEqual(self.namespace.data, {})

    def test_namespace_load_data(self):
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.load_data("foo", "bar")

    def test_namespace_unload_data(self):
        self.namespace.data = {"key1": "value1", "key2": "value2"}
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.unload_data("key1")
        self.assertNotIn("key1", self.namespace.data)
        self.assertIn("key2", self.namespace.data)

    def test_namespace_get_position_of_last_item(self):
        self.namespace.data = {"key1": "val1", "key2": "val2", "key3": "val3"}
        self.assertEqual(self.namespace.get_position_of_last_item_in_data(), 2)
        self.namespace.data = {}
        self.assertEqual(self.namespace.get_position_of_last_item_in_data(), -1)

    def test_namespace_set_persistence_generic(self):
        self.namespace.set_persistence("genericSkill")
        self.assertEqual(self.namespace.duration, 30)
        self.assertFalse(self.namespace.persistent)

    def test_namespace_set_persistence_idle(self):
        self.namespace.set_persistence("idleDisplaySkill")
        self.assertEqual(self.namespace.duration, 0)
        self.assertTrue(self.namespace.persistent)


class TestNamespaceManager(TestCase):
    """Tests for NamespaceManager with session_id-only architecture."""

    def setUp(self):
        self.namespace_manager = NamespaceManager(FakeBus())

    def tearDown(self):
        # cancel any pending auto-removal timers so they don't fire post-test
        for session in self.namespace_manager.sessions.values():
            for timer in session.remove_namespace_timers.values():
                timer.cancel()

    def test_handle_clear_namespace_active(self):
        namespace = Namespace("foo")
        namespace.remove = mock.Mock()
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces = dict(foo=namespace)
        session.active_namespaces = [namespace]

        message = Message("gui.clear.namespace", data={"__from": "foo"})
        self.namespace_manager.handle_clear_namespace(message)
        namespace.remove.assert_called()

    def test_handle_clear_namespace_inactive(self):
        message = Message("gui.clear.namespace", data={"__from": "foo"})
        namespace = Namespace("foo")
        namespace.remove = mock.Mock()
        self.namespace_manager.handle_clear_namespace(message)
        namespace.remove.assert_not_called()

    def test_parse_persistence(self):
        self.assertEqual(self.namespace_manager._parse_persistence(True), (True, 0))
        self.assertEqual(self.namespace_manager._parse_persistence(False), (False, 0))
        self.assertEqual(self.namespace_manager._parse_persistence(None), (False, 30))
        self.assertEqual(self.namespace_manager._parse_persistence(10), (False, 10))
        self.assertEqual(self.namespace_manager._parse_persistence(1.0), (False, 1))
        with self.assertRaises(ValueError):
            self.namespace_manager._parse_persistence(-10)

    def test_handle_show_page_template_routing(self):
        """SYSTEM_* templates are routed to adapters."""
        self.namespace_manager._dispatch_template_to_adapters = Mock()
        message = Message("gui.page.show", data={
            "__from": "test_skill", "__idle": 10, "page_names": ["SYSTEM_weather"]
        })
        self.namespace_manager.handle_show_page(message)
        self.namespace_manager._dispatch_template_to_adapters.assert_called()

    def test_handle_show_page_non_template_rejected(self):
        """Non-SYSTEM_* page names are rejected."""
        message = Message("gui.page.show", data={
            "__from": "foo", "__idle": 10, "page_names": ["bar.qml"]
        })
        with mock.patch(f'{PATCH_MODULE}.LOG') as mock_log:
            self.namespace_manager.handle_show_page(message)
            mock_log.error.assert_called()

    def test_handle_show_page_invalid_message(self):
        message = Message("gui.page.show", data={"__from": "foo"})
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager.handle_show_page(message)
        session = self.namespace_manager.get_session("default")
        self.assertListEqual([], session.active_namespaces)
        self.assertDictEqual({}, session.loaded_namespaces)

    def test_ensure_namespace_exists(self):
        session = self.namespace_manager.get_session("default")
        ns = self.namespace_manager._ensure_namespace_exists("new_skill", session)
        self.assertIsNotNone(ns)
        self.assertEqual(ns.skill_id, "new_skill")
        self.assertIn("new_skill", session.loaded_namespaces)

    def test_update_namespace_persistence(self):
        ns = Namespace("test")
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces["test"] = ns
        session.active_namespaces = [ns]
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager._update_namespace_persistence(15, session)
        self.assertEqual(ns.duration, 15)
        self.assertFalse(ns.persistent)

    def test_remove_namespace(self):
        ns = Namespace("test")
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces["test"] = ns
        session.active_namespaces.append(ns)
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager._remove_namespace("test", session, "default")
        self.assertNotIn(ns, session.active_namespaces)

    def test_handle_set_value(self):
        ns = Namespace("test")
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces["test"] = ns

        mock_adapter = Mock()
        self.namespace_manager.adapters = [mock_adapter]

        message = Message("gui.value.set", data={"__from": "test", "key": "value"})
        self.namespace_manager.handle_set_value(message)

        self.assertEqual(ns.data["key"], "value")
        # adapter notified with (skill_id, filtered_data, session_id) -- no __from
        mock_adapter.on_session_update.assert_called_once_with(
            "test", {"key": "value"}, "default")

    def test_forward_to_gui_status_event(self):
        """Status events are forwarded to adapters with the session_id."""
        mock_adapter = mock.Mock()
        self.namespace_manager.adapters = [mock_adapter]

        message = Message("test.event", data={"test": "data"})
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager.forward_to_gui(message)

        mock_adapter.on_status_event.assert_called_once_with(
            "test.event", {"test": "data"}, "default")

    def test_dispatch_template_to_adapters(self):
        """Templates are dispatched with session_id only (no site_id)."""
        mock_adapter = mock.Mock()
        self.namespace_manager.adapters = [mock_adapter]

        self.namespace_manager._dispatch_template_to_adapters(
            "SYSTEM_weather", "test_skill", {"current_temp": 22}, "session1"
        )
        mock_adapter.dispatch_template.assert_called_once_with(
            "SYSTEM_weather", "test_skill", {"current_temp": 22}, "session1"
        )

    def test_activate_namespace_already_active(self):
        ns = Namespace("existing")
        other_ns = Namespace("other")
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces["existing"] = ns
        session.loaded_namespaces["other"] = other_ns
        session.active_namespaces = [other_ns, ns]

        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager._activate_namespace("existing", session, "default")
        self.assertEqual(session.active_namespaces[0].skill_id, "existing")

    def test_session_id_extraction(self):
        """The routing key is the session_id; default when absent."""
        self.assertEqual(self.namespace_manager._session_id(Message("test")), "default")
        msg = Message("test", context={"session": {"session_id": "sid1"}})
        self.assertEqual(self.namespace_manager._session_id(msg), "sid1")
        # missing/None session_id falls back to "default"
        msg2 = Message("test", context={"session": {}})
        self.assertEqual(self.namespace_manager._session_id(msg2), "default")

    def test_session_isolation(self):
        """Two different session_ids keep independent state."""
        msg1 = Message("gui.value.set", data={"__from": "skill", "val": 1},
                       context={"session": {"session_id": "room1"}})
        msg2 = Message("gui.value.set", data={"__from": "skill", "val": 2},
                       context={"session": {"session_id": "room2"}})

        self.namespace_manager.handle_set_value(msg1)
        self.namespace_manager.handle_set_value(msg2)

        session1 = self.namespace_manager.get_session("room1")
        session2 = self.namespace_manager.get_session("room2")
        self.assertEqual(session1.loaded_namespaces["skill"].data["val"], 1)
        self.assertEqual(session2.loaded_namespaces["skill"].data["val"], 2)

    def test_shared_session_id_shares_state(self):
        """Two clients sharing one session_id share the same session/stack."""
        msg1 = Message("gui.page.show", data={
            "page_names": ["SYSTEM_weather"], "__from": "weather.skill", "__idle": 30
        }, context={"session": {"session_id": "shared"}})
        msg2 = Message("gui.value.set", data={"__from": "weather.skill", "temp": 21},
                       context={"session": {"session_id": "shared"}})

        self.namespace_manager.handle_show_page(msg1)
        self.namespace_manager.handle_set_value(msg2)

        # both messages addressed the same session -> one session, shared data
        self.assertEqual(self.namespace_manager.get_all_sessions(), ["shared"])
        data = self.namespace_manager.get_namespace_data("weather.skill", "shared")
        self.assertEqual(data["temp"], 21)

    # ====== State Query API Tests ======

    def test_get_active_namespace_empty_session(self):
        self.assertIsNone(self.namespace_manager.get_active_namespace("default"))

    def test_get_active_namespace_returns_top_of_stack(self):
        msg = Message("gui.page.show", data={
            "page_names": ["SYSTEM_weather"], "__from": "weather.skill", "__idle": 30
        }, context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_show_page(msg)
        active = self.namespace_manager.get_active_namespace("default")
        self.assertIsNotNone(active)
        self.assertEqual(active.skill_id, "weather.skill")

    def test_get_active_namespace_different_sessions(self):
        msg1 = Message("gui.page.show", data={
            "page_names": ["SYSTEM_weather"], "__from": "weather.skill", "__idle": 30
        }, context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_show_page(msg1)
        msg2 = Message("gui.page.show", data={
            "page_names": ["SYSTEM_clock"], "__from": "clock.skill", "__idle": 30
        }, context={"session": {"session_id": "kitchen"}})
        self.namespace_manager.handle_show_page(msg2)

        self.assertEqual(self.namespace_manager.get_active_namespace("default").skill_id, "weather.skill")
        self.assertEqual(self.namespace_manager.get_active_namespace("kitchen").skill_id, "clock.skill")

    def test_get_namespace_data_returns_none_for_missing(self):
        self.assertIsNone(self.namespace_manager.get_namespace_data("nope.skill", "default"))

    def test_get_namespace_data_returns_session_data(self):
        msg = Message("gui.page.show", data={
            "page_names": ["SYSTEM_weather"], "__from": "weather.skill", "__idle": 30
        }, context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_show_page(msg)
        set_msg = Message("gui.value.set", data={
            "__from": "weather.skill", "current_temp": 22, "condition": "sunny"
        }, context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_set_value(set_msg)

        data = self.namespace_manager.get_namespace_data("weather.skill", "default")
        self.assertEqual(data["current_temp"], 22)
        self.assertEqual(data["condition"], "sunny")

    def test_get_namespace_data_is_copy(self):
        msg = Message("gui.page.show", data={
            "page_names": ["SYSTEM_text"], "__from": "test.skill", "__idle": 30
        }, context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_show_page(msg)
        set_msg = Message("gui.value.set", data={"__from": "test.skill", "text": "original"},
                          context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_set_value(set_msg)

        data = self.namespace_manager.get_namespace_data("test.skill", "default")
        data["text"] = "modified"
        data2 = self.namespace_manager.get_namespace_data("test.skill", "default")
        self.assertEqual(data2["text"], "original")

    def test_get_all_sessions_empty(self):
        self.assertEqual(self.namespace_manager.get_all_sessions(), [])

    def test_get_all_sessions_returns_all(self):
        for sid, skill, tpl in [("default", "weather.skill", "SYSTEM_weather"),
                                ("kitchen", "clock.skill", "SYSTEM_clock"),
                                ("bedroom", "text.skill", "SYSTEM_text")]:
            msg = Message("gui.page.show", data={
                "page_names": [tpl], "__from": skill, "__idle": 30
            }, context={"session": {"session_id": sid}})
            self.namespace_manager.handle_show_page(msg)

        sessions = self.namespace_manager.get_all_sessions()
        self.assertEqual(len(sessions), 3)
        self.assertIn("default", sessions)
        self.assertIn("kitchen", sessions)
        self.assertIn("bedroom", sessions)

    def test_is_namespace_active_returns_false_when_inactive(self):
        self.assertFalse(self.namespace_manager.is_namespace_active("nope.skill", "default"))

    def test_is_namespace_active_returns_true_for_active(self):
        msg = Message("gui.page.show", data={
            "page_names": ["SYSTEM_weather"], "__from": "weather.skill", "__idle": 30
        }, context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_show_page(msg)
        self.assertTrue(self.namespace_manager.is_namespace_active("weather.skill", "default"))

    def test_is_namespace_active_returns_false_for_lower_stack(self):
        msg1 = Message("gui.page.show", data={
            "page_names": ["SYSTEM_weather"], "__from": "weather.skill", "__idle": 30
        }, context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_show_page(msg1)
        msg2 = Message("gui.page.show", data={
            "page_names": ["SYSTEM_text"], "__from": "text.skill", "__idle": 30
        }, context={"session": {"session_id": "default"}})
        self.namespace_manager.handle_show_page(msg2)

        self.assertFalse(self.namespace_manager.is_namespace_active("weather.skill", "default"))
        self.assertTrue(self.namespace_manager.is_namespace_active("text.skill", "default"))
