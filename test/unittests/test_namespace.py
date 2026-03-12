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
"""Tests for the GUI namespace helper class."""
from unittest import TestCase, mock
from unittest.mock import Mock

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

from ovos_gui.namespace import Namespace, NamespaceManager, _validate_page_message
from ovos_gui.page import GuiPage

PATCH_MODULE = "ovos_gui.namespace"


class TestNamespaceFunctions(TestCase):
    def test_validate_page_message(self):
        """Test _validate_page_message function."""
        # Valid template message
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

        # Missing __idle is NOT an error for validation (only page_names and __from)
        invalid3 = Message("gui.page.show", data={"page_names": ["SYSTEM_weather"], "__from": "skill_id"})
        self.assertTrue(_validate_page_message(invalid3))


class TestNamespace(TestCase):
    """Tests for Namespace class."""

    def setUp(self):
        self.namespace = Namespace("test_skill")

    def test_namespace_initialization(self):
        """Test that namespace initializes with correct defaults."""
        ns = Namespace("foo_skill")
        self.assertEqual(ns.skill_id, "foo_skill")
        self.assertFalse(ns.persistent)
        self.assertEqual(ns.duration, 30)
        self.assertEqual(ns.data, {})
        self.assertFalse(ns.session_set)

    def test_namespace_add(self):
        """Test that add() method works."""
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.add()

    def test_namespace_activate(self):
        """Test that activate() method works."""
        self.namespace.pages = [GuiPage(name="test", persistent=True, duration=0)]
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.activate(position=0)

    def test_namespace_remove(self):
        """Test that remove() method clears namespace state."""
        self.namespace.data = {"key1": "value1", "key2": "value2"}
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.remove(position=0)
        # Verify state was cleared
        self.assertEqual(self.namespace.data, {})

    def test_namespace_load_data(self):
        """Test load_data method stores data in namespace."""
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.load_data("foo", "bar")

    def test_namespace_unload_data(self):
        """Test unload_data method removes data from namespace."""
        self.namespace.data = {"key1": "value1", "key2": "value2"}
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace.unload_data("key1")
        self.assertNotIn("key1", self.namespace.data)
        self.assertIn("key2", self.namespace.data)

    def test_namespace_get_position_of_last_item(self):
        """Test getting position of last item in data."""
        self.namespace.data = {"key1": "val1", "key2": "val2", "key3": "val3"}
        position = self.namespace.get_position_of_last_item_in_data()
        self.assertEqual(position, 2)

        self.namespace.data = {}
        position = self.namespace.get_position_of_last_item_in_data()
        self.assertEqual(position, -1)

    def test_namespace_set_persistence_generic(self):
        """Test setting persistence for generic skill."""
        self.namespace.set_persistence("genericSkill")
        self.assertEqual(self.namespace.duration, 30)
        self.assertFalse(self.namespace.persistent)

    def test_namespace_set_persistence_idle(self):
        """Test setting persistence for idle skill."""
        self.namespace.set_persistence("idleDisplaySkill")
        self.assertEqual(self.namespace.duration, 0)
        self.assertTrue(self.namespace.persistent)


class TestNamespaceManager(TestCase):
    """Tests for NamespaceManager with session-aware architecture."""

    def setUp(self):
        self.namespace_manager = NamespaceManager(FakeBus())

    def test_handle_clear_namespace_active(self):
        """Test clearing an active namespace."""
        namespace = Namespace("foo")
        namespace.remove = mock.Mock()
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces = dict(foo=namespace)
        session.active_namespaces = [namespace]

        message = Message("gui.clear.namespace", data={"__from": "foo"})
        self.namespace_manager.handle_clear_namespace(message)
        namespace.remove.assert_called()

    def test_handle_clear_namespace_inactive(self):
        """Test clearing a namespace that's not active."""
        message = Message("gui.clear.namespace", data={"__from": "foo"})
        namespace = Namespace("foo")
        namespace.remove = mock.Mock()
        self.namespace_manager.handle_clear_namespace(message)
        namespace.remove.assert_not_called()

    def test_parse_persistence(self):
        """Test parsing persistence configuration."""
        self.assertEqual(self.namespace_manager._parse_persistence(True),
                         (True, 0))
        self.assertEqual(self.namespace_manager._parse_persistence(False),
                         (False, 0))
        self.assertEqual(self.namespace_manager._parse_persistence(None),
                         (False, 30))
        self.assertEqual(self.namespace_manager._parse_persistence(10),
                         (False, 10))
        self.assertEqual(self.namespace_manager._parse_persistence(1.0),
                         (False, 1))
        with self.assertRaises(ValueError):
            self.namespace_manager._parse_persistence(-10)

    def test_handle_show_page_template_routing(self):
        """Test that SYSTEM_* templates are routed to adapters."""
        self.namespace_manager._dispatch_template_to_adapters = Mock()

        # Template-based message (SYSTEM_*)
        message = Message("gui.page.show", data={
            "__from": "test_skill",
            "__idle": 10,
            "page_names": ["SYSTEM_weather"]
        })

        self.namespace_manager.handle_show_page(message)

        # Verify dispatch_template was called
        self.namespace_manager._dispatch_template_to_adapters.assert_called()

    def test_handle_show_page_non_template_rejected(self):
        """Test that non-SYSTEM_* page names are rejected."""
        message = Message("gui.page.show", data={
            "__from": "foo",
            "__idle": 10,
            "page_names": ["bar.qml"]
        })
        with mock.patch(f'{PATCH_MODULE}.LOG') as mock_log:
            self.namespace_manager.handle_show_page(message)
            # Should log an error about non-template page name
            mock_log.error.assert_called()

    def test_handle_show_page_invalid_message(self):
        """Test handler with invalid message."""
        message_data = {"__from": "foo"}
        message = Message("gui.page.show", data=message_data)
        
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager.handle_show_page(message)

        session = self.namespace_manager.get_session("default")
        self.assertListEqual([], session.active_namespaces)
        self.assertDictEqual({}, session.loaded_namespaces)

    def test_ensure_namespace_exists(self):
        """Test ensuring namespace exists or is created."""
        session = self.namespace_manager.get_session("default")
        ns = self.namespace_manager._ensure_namespace_exists("new_skill", session)
        self.assertIsNotNone(ns)
        self.assertEqual(ns.skill_id, "new_skill")
        self.assertIn("new_skill", session.loaded_namespaces)

    def test_update_namespace_persistence(self):
        """Test updating namespace persistence."""
        ns = Namespace("test")
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces["test"] = ns
        session.active_namespaces = [ns]
        
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager._update_namespace_persistence(15, session)
        
        self.assertEqual(ns.duration, 15)
        self.assertFalse(ns.persistent)

    def test_remove_namespace(self):
        """Test removing a namespace."""
        ns = Namespace("test")
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces["test"] = ns
        session.active_namespaces.append(ns)
        
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager._remove_namespace("test", session, "default", "default")
            
        self.assertNotIn(ns, session.active_namespaces)

    def test_handle_set_value(self):
        """Test set value handler."""
        ns = Namespace("test")
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces["test"] = ns
        
        mock_adapter = Mock()
        self.namespace_manager.adapters = [mock_adapter]
        
        message = Message("gui.value.set", data={"__from": "test", "key": "value"})
        self.namespace_manager.handle_set_value(message)
        
        self.assertEqual(ns.data["key"], "value")
        # Verify adapter notified
        mock_adapter.on_session_update.assert_called()

    def test_forward_to_gui_system_event(self):
        """Test forwarding system status events to GUI."""
        mock_adapter = mock.Mock()
        self.namespace_manager.adapters = [mock_adapter]

        message = Message("test.event", data={"test": "data"})
        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager.forward_to_gui(message)

        # Verify adapter's on_status_event was called with session/site info
        mock_adapter.on_status_event.assert_called()

    def test_dispatch_template_to_adapters(self):
        """Test dispatching template to adapters."""
        mock_adapter = mock.Mock()
        self.namespace_manager.adapters = [mock_adapter]

        # Dispatch a template
        self.namespace_manager._dispatch_template_to_adapters(
            "SYSTEM_weather", "test_skill", {"current_temp": 22}, "session1", "site1"
        )

        # Verify adapter dispatch_template was called with all args
        mock_adapter.dispatch_template.assert_called_with(
            "SYSTEM_weather", "test_skill", {"current_temp": 22}, "session1", "site1"
        )

    def test_activate_namespace_already_active(self):
        """Test activating a namespace that's already in active_namespaces."""
        ns = Namespace("existing")
        other_ns = Namespace("other")
        session = self.namespace_manager.get_session("default")
        session.loaded_namespaces["existing"] = ns
        session.loaded_namespaces["other"] = other_ns
        session.active_namespaces = [other_ns, ns]

        with mock.patch(f'{PATCH_MODULE}.LOG'):
            self.namespace_manager._activate_namespace("existing", session, "default", "default")

        # Verify it's now at position 0
        self.assertEqual(session.active_namespaces[0].skill_id, "existing")

    def test_get_routing_info(self):
        """Test _get_routing_info extraction."""
        # Case 1: Empty context
        message = Message("test")
        sid, site = self.namespace_manager._get_routing_info(message)
        self.assertEqual(sid, "default")
        self.assertEqual(site, "unknown")

        # Case 2: Provided context
        message = Message("test", context={"session": {"session_id": "sid1", "site_id": "site1"}})
        sid, site = self.namespace_manager._get_routing_info(message)
        self.assertEqual(sid, "sid1")
        self.assertEqual(site, "site1")

    def test_get_session_key(self):
        """Test session isolation logic."""
        # site_id takes priority if meaningful
        key = self.namespace_manager._get_session_key("sid1", "site1")
        self.assertEqual(key, "site1")
        
        # fallback to session_id if site is unknown
        key = self.namespace_manager._get_session_key("sid1", "unknown")
        self.assertEqual(key, "sid1")
        
        key = self.namespace_manager._get_session_key("sid1", None)
        self.assertEqual(key, "sid1")

    def test_session_isolation(self):
        """Verify that two different sessions have independent state."""
        msg1 = Message("gui.value.set", data={"__from": "skill", "val": 1}, 
                       context={"session": {"site_id": "room1"}})
        msg2 = Message("gui.value.set", data={"__from": "skill", "val": 2}, 
                       context={"session": {"site_id": "room2"}})
        
        self.namespace_manager.handle_set_value(msg1)
        self.namespace_manager.handle_set_value(msg2)
        
        session1 = self.namespace_manager.get_session("room1")
        session2 = self.namespace_manager.get_session("room2")
        
        self.assertEqual(session1.loaded_namespaces["skill"].data["val"], 1)
        self.assertEqual(session2.loaded_namespaces["skill"].data["val"], 2)
        self.assertIsNot(session1, session2)
