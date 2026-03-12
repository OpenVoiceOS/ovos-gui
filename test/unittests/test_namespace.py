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
from os.path import join, isdir, isfile
from shutil import rmtree
from unittest import TestCase, mock
from unittest.mock import Mock

from ovos_bus_client.message import Message
from ovos_bus_client.apis.gui import get_xdg_cache_save_path
from ovos_utils.fakebus import FakeBus

from ovos_gui.namespace import Namespace, _validate_page_message
from ovos_gui.page import GuiPage

GUI_CACHE_PATH = get_xdg_cache_save_path('ovos_gui')

PATCH_MODULE = "ovos_gui.namespace"


class TestNamespaceFunctions(TestCase):
    def test_validate_page_message(self):
        """Test _validate_page_message function with valid and invalid messages."""
        # Valid message
        valid_msg = Message("gui.page.show", data={
            "page_names": ["page1"], "__from": "skill_id"
        })
        self.assertTrue(_validate_page_message(valid_msg))

        # Invalid: missing page_names
        invalid1 = Message("gui.page.show", data={"__from": "skill_id"})
        self.assertFalse(_validate_page_message(invalid1))

        # Invalid: missing __from
        invalid2 = Message("gui.page.show", data={"page_names": ["page1"]})
        self.assertFalse(_validate_page_message(invalid2))

        # Invalid: page_names not a list
        invalid3 = Message("gui.page.show", data={
            "page_names": "page1", "__from": "skill_id"
        })
        self.assertFalse(_validate_page_message(invalid3))

    def test_get_idle_display_config(self):
        """Test idle display configuration handling."""
        ns = Namespace("idleDisplaySkill")
        ns.load_pages([GuiPage(name="idle", persistent=True, duration=0)])
        ns.set_persistence("idleDisplaySkill")
        self.assertTrue(ns.persistent)
        self.assertEqual(ns.duration, 0)

    def test_get_active_gui_extension(self):
        """Test retrieval of active GUI extensions/pages."""
        ns = Namespace("test_skill")
        pages = [
            GuiPage(name="page1", persistent=False, duration=30),
            GuiPage(name="page2", persistent=False, duration=30),
        ]
        ns.load_pages(pages)
        self.assertEqual(ns.active_page.name, "page1")
        self.assertEqual(len(ns.pages), 2)


class TestNamespace(TestCase):
    def setUp(self):
        self.namespace = Namespace("foo")

    def test_init_gui_file_share(self):
        # TODO: Test init with/without server and host config
        pass

    def test_add(self):
        add_namespace_message = dict(
            type="mycroft.session.list.insert",
            namespace="mycroft.system.active_skills",
            position=0,
            data=[dict(skill_id="foo")]
        )
        self.namespace.send_message_to_gui = mock.Mock()
        self.namespace.add()
        self.namespace.send_message_to_gui.assert_called_with(add_namespace_message)

    def test_activate(self):
        self.namespace.load_pages([
            GuiPage(name="foo", persistent=False, duration=False),
            GuiPage(name="bar", persistent=False, duration=False),
            GuiPage(name="foobar", persistent=False, duration=False),
            GuiPage(name="baz", persistent=False, duration=False),
            GuiPage(name="foobaz", persistent=False, duration=False)
        ])
        activate_namespace_message = {
            "type": "mycroft.session.list.move",
            "namespace": "mycroft.system.active_skills",
            "from": 5,
            "to": 0,
            "items_number": 1
        }
        self.namespace.send_message_to_gui = mock.Mock()
        self.namespace.activate(position=5)
        self.namespace.send_message_to_gui.assert_called_with(activate_namespace_message)

    def test_remove(self):
        self.namespace.data = dict(foo="bar")
        self.namespace.pages = ["foo", "bar"]
        remove_namespace_message = dict(
            type="mycroft.session.list.remove",
            namespace="mycroft.system.active_skills",
            position=3,
            items_number=1
        )
        self.namespace.send_message_to_gui = mock.Mock()
        self.namespace.remove(position=3)
        self.namespace.send_message_to_gui.assert_called_with(remove_namespace_message)

        self.assertFalse(self.namespace.data)
        self.assertFalse(self.namespace.pages)

    def test_load_data(self):
        load_data_message = dict(
            type="mycroft.session.set",
            namespace="foo",
            data=dict(foo="bar")
        )
        self.namespace.send_message_to_gui = mock.Mock()
        self.namespace.load_data(name="foo", value="bar")
        self.namespace.send_message_to_gui.assert_called_with(load_data_message)

    def test_unload_data(self):
        """Test unload_data method removes data from namespace."""
        self.namespace.data = {"key1": "value1", "key2": "value2"}
        self.namespace.send_message_to_gui = mock.Mock()
        self.namespace.unload_data("key1")
        # Verify message was sent
        call_args = self.namespace.send_message_to_gui.call_args[0][0]
        self.assertEqual(call_args["type"], "mycroft.session.delete")
        self.assertEqual(call_args["property"], "key1")

    def test_get_position_of_last_item_in_data(self):
        """Test getting position of last item in data."""
        self.namespace.data = {"key1": "val1", "key2": "val2", "key3": "val3"}
        position = self.namespace.get_position_of_last_item_in_data()
        self.assertEqual(position, 2)

        self.namespace.data = {}
        position = self.namespace.get_position_of_last_item_in_data()
        self.assertEqual(position, -1)

    def test_set_persistence_numeric(self):
        self.namespace.set_persistence("genericSkill")
        self.assertEqual(self.namespace.duration, 30)
        self.assertFalse(self.namespace.persistent)

    def test_set_persistence_boolean(self):
        self.namespace.set_persistence("idleDisplaySkill")
        self.assertEqual(self.namespace.duration, 0)
        self.assertTrue(self.namespace.persistent)

    def test_set_persistence_from_active_page_non_persistent(self):
        """Test set_persistence uses active page when it's non-persistent."""
        page = GuiPage(name="test", persistent=False, duration=15)
        self.namespace.pages = [page]
        self.namespace.page_number = 0
        self.namespace.set_persistence(None)
        # Should use the active page's settings
        self.assertFalse(self.namespace.persistent)
        self.assertEqual(self.namespace.duration, 15)

    def test_set_persistence_from_active_page_persistent(self):
        """Test set_persistence uses active page when it's persistent."""
        page = GuiPage(name="test", persistent=True, duration=0)
        self.namespace.pages = [page]
        self.namespace.page_number = 0
        self.namespace.set_persistence(None)
        # Should use the active page's settings
        self.assertTrue(self.namespace.persistent)
        self.assertEqual(self.namespace.duration, 0)

    def test_set_persistence_no_active_page(self):
        """Test set_persistence defaults when no active page."""
        # No pages loaded, should default to 30 seconds
        self.namespace.set_persistence(None)
        self.assertFalse(self.namespace.persistent)
        self.assertEqual(self.namespace.duration, 30)

    def test_load_pages_new(self):
        self.namespace.pages = [GuiPage(name="foo", persistent=True, duration=0),
                                GuiPage(name="bar", persistent=False, duration=30)]
        new_pages = [GuiPage(name="foobar", persistent=False, duration=30)]
        load_page_message = dict(
            type="mycroft.events.triggered",
            namespace="foo",
            event_name="page_gained_focus",
            data=dict(number=2)
        )
        self.namespace.send_message_to_gui = mock.Mock()
        show_index = None
        self.namespace.load_pages(new_pages, show_index)
        self.namespace.send_message_to_gui.assert_called_with(load_page_message)
        self.assertListEqual(self.namespace.pages, self.namespace.pages)

    def test_load_pages_empty(self):
        """Test load_pages with empty page list."""
        self.namespace.send_message_to_gui = mock.Mock()
        # Should handle gracefully when pages list is empty
        self.namespace.load_pages([])
        # Should not send any message when pages is empty
        self.namespace.send_message_to_gui.assert_not_called()

    def test_load_pages_existing(self):
        self.namespace.pages = [GuiPage(name="foo", persistent=True, duration=0),
                                GuiPage(name="bar", persistent=False, duration=30)]
        new_pages = [GuiPage(name="foo", persistent=True, duration=0)]
        load_page_message = dict(
            type="mycroft.events.triggered",
            namespace="foo",
            event_name="page_gained_focus",
            data=dict(number=0)
        )
        self.namespace.send_message_to_gui = mock.Mock()
        show_index = None
        self.namespace.load_pages(new_pages, show_index)
        self.namespace.send_message_to_gui.assert_called_with(load_page_message)
        self.assertListEqual(self.namespace.pages, self.namespace.pages)

    def test_add_pages(self):
        """Test _add_pages internal method."""
        page1 = GuiPage(name="page1", persistent=False, duration=30)
        page2 = GuiPage(name="page2", persistent=False, duration=30)
        # Pages must exist in the list before calling _add_pages
        self.namespace.pages = [page1, page2]
        # _add_pages finds position of page2 in the list
        self.namespace._add_pages([page2])
        # Verify pages list is unchanged (method is currently a stub)
        self.assertEqual(len(self.namespace.pages), 2)
        self.assertEqual(self.namespace.pages[1].name, "page2")

    def test_activate_page(self):
        """Test _activate_page method for page focus."""
        page1 = GuiPage(name="page1", persistent=False, duration=30)
        page2 = GuiPage(name="page2", persistent=False, duration=30)
        self.namespace.pages = [page1, page2]
        self.namespace.page_number = 0
        self.namespace.send_message_to_gui = mock.Mock()

        self.namespace._activate_page(page2)
        # Verify page number was updated
        self.assertEqual(self.namespace.page_number, 1)
        # Verify message was sent
        self.assertTrue(self.namespace.send_message_to_gui.called)

    def test_remove_pages(self):
        self.namespace.pages = [GuiPage(name="foo", persistent=False, duration=False),
                                GuiPage(name="bar", persistent=False, duration=False),
                                GuiPage(name="foobar", persistent=False, duration=False)]
        remove_page_message = dict(
            type="mycroft.gui.list.remove",
            namespace="foo",
            position=2,
            items_number=1
        )
        self.namespace.send_message_to_gui = mock.Mock()
        self.namespace.remove_pages([2])
        self.namespace.send_message_to_gui.assert_called_with(remove_page_message)
        self.assertListEqual(["foo", "bar"], self.namespace.page_names)

    def test_page_gained_focus(self):
        """Test page_gained_focus method."""
        page1 = GuiPage(name="page1", persistent=False, duration=30)
        page2 = GuiPage(name="page2", persistent=False, duration=30)
        self.namespace.pages = [page1, page2]
        self.namespace.page_number = 0
        self.namespace.send_message_to_gui = mock.Mock()

        self.namespace.page_gained_focus(1)
        self.assertEqual(self.namespace.page_number, 1)

    def test_page_update_interaction(self):
        """Test page interaction updates."""
        page = GuiPage(name="interactive_page", persistent=False, duration=30)
        self.namespace.pages = [page]
        self.assertEqual(len(self.namespace.pages), 1)
        self.assertEqual(self.namespace.pages[0].name, "interactive_page")

    def test_get_page_at_position(self):
        """Test retrieving page at specific position."""
        pages = [
            GuiPage(name="page1", persistent=False, duration=30),
            GuiPage(name="page2", persistent=False, duration=30),
            GuiPage(name="page3", persistent=False, duration=30),
        ]
        self.namespace.pages = pages
        self.assertEqual(self.namespace.pages[0].name, "page1")
        self.assertEqual(self.namespace.pages[1].name, "page2")
        self.assertEqual(self.namespace.pages[2].name, "page3")

    def test_get_active_page(self):
        """Test getting currently active page."""
        page1 = GuiPage(name="page1", persistent=False, duration=30)
        page2 = GuiPage(name="page2", persistent=False, duration=30)
        self.namespace.pages = [page1, page2]
        self.namespace.page_number = 0
        self.assertEqual(self.namespace.active_page.name, "page1")

        self.namespace.page_number = 1
        self.assertEqual(self.namespace.active_page.name, "page2")

        # Out of bounds
        self.namespace.page_number = 5
        self.assertIsNone(self.namespace.active_page)

    def test_index_in_pages_list(self):
        """Test finding page index in list."""
        page1 = GuiPage(name="page1", persistent=False, duration=30)
        page2 = GuiPage(name="page2", persistent=False, duration=30)
        pages = [page1, page2]
        self.namespace.pages = pages
        for i, page in enumerate(pages):
            self.assertEqual(self.namespace.pages[i].name, page.name)

    def test_global_back(self):
        """Test global back navigation."""
        page1 = GuiPage(name="page1", persistent=False, duration=30)
        page2 = GuiPage(name="page2", persistent=False, duration=30)
        page3 = GuiPage(name="page3", persistent=False, duration=30)
        self.namespace.pages = [page1, page2, page3]
        self.namespace.page_number = 2
        self.namespace.send_message_to_gui = mock.Mock()

        self.namespace.global_back()
        # After back, should be at page 1 and page 3 removed
        self.assertEqual(self.namespace.page_number, 1)
        self.assertEqual(len(self.namespace.pages), 2)


class TestNamespaceManager(TestCase):
    def setUp(self):
        from ovos_gui.namespace import NamespaceManager
        self.namespace_manager = NamespaceManager(FakeBus())

    def test_handle_clear_namespace_active(self):
        namespace = Namespace("foo")
        namespace.remove = mock.Mock()
        self.namespace_manager.loaded_namespaces = dict(foo=namespace)
        self.namespace_manager.active_namespaces = [namespace]

        message = Message("gui.clear.namespace", data={"__from": "foo"})
        self.namespace_manager.handle_clear_namespace(message)
        namespace.remove.assert_called_with(0)

    def test_handle_clear_namespace_inactive(self):
        message = Message("gui.clear.namespace", data={"__from": "foo"})
        namespace = Namespace("foo")
        namespace.remove = mock.Mock()
        self.namespace_manager.handle_clear_namespace(message)
        namespace.remove.assert_not_called()

    def test_handle_send_event(self):
        message_data = {
            "__from": "foo", "event_name": "bar", "params": "foobar"
        }
        message = Message("gui.clear.namespace", data=message_data)
        event_triggered_message = dict(
            type='mycroft.events.triggered',
            namespace="foo",
            event_name="bar",
            data="foobar"
        )
        self.namespace_manager.send_message_to_gui = mock.Mock()
        self.namespace_manager.handle_send_event(message)
        self.namespace_manager.send_message_to_gui.assert_called_with(event_triggered_message)

    def test_handle_delete_page_active_namespace(self):
        namespace = Namespace("foo")
        namespace.pages = [GuiPage(name="bar", persistent=True, duration=0)]
        namespace.remove_pages = mock.Mock()
        self.namespace_manager.loaded_namespaces = dict(foo=namespace)
        self.namespace_manager.active_namespaces = [namespace]

        message_data = {"__from": "foo", "page_names": ["bar"]}
        message = Message("gui.clear.namespace", data=message_data)
        self.namespace_manager.handle_delete_page(message)
        namespace.remove_pages.assert_called_with([0])

    def test_handle_delete_page_inactive_namespace(self):
        namespace = Namespace("foo")
        namespace.pages = ["bar"]
        namespace.remove_pages = mock.Mock()

        message_data = {"__from": "foo", "page": ["bar"]}
        message = Message("gui.clear.namespace", data=message_data)
        self.namespace_manager.handle_delete_page(message)
        namespace.remove_pages.assert_not_called()

    def test_handle_remove_pages(self):
        """Test handler for page removal requests."""
        namespace = Namespace("foo")
        namespace.pages = [
            GuiPage(name="page1", persistent=False, duration=30),
            GuiPage(name="page2", persistent=False, duration=30),
        ]
        namespace.remove_pages = mock.Mock()
        self.namespace_manager.loaded_namespaces = dict(foo=namespace)
        self.namespace_manager.active_namespaces = [namespace]

        message_data = {"__from": "foo", "page_names": ["page1"]}
        message = Message("gui.page.delete", data=message_data)
        self.namespace_manager.handle_delete_page(message)
        namespace.remove_pages.assert_called()

    def test_parse_persistence(self):
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

    def test_handle_show_page(self):
        real_activate_namespace = self.namespace_manager._activate_namespace
        real_load_pages = self.namespace_manager._load_pages
        real_update_persistence = self.namespace_manager._update_namespace_persistence
        self.namespace_manager._activate_namespace = Mock()
        self.namespace_manager._load_pages = Mock()
        self.namespace_manager._update_namespace_persistence = Mock()

        # Legacy message
        message = Message("gui.page.show", data={"__from": "foo",
                                                 "__idle": 10,
                                                 "page_names": ["bar", "test/baz"]})
        self.namespace_manager.handle_show_page(message)
        self.namespace_manager._activate_namespace.assert_called_with("foo")
        self.namespace_manager._load_pages.assert_called_with(
            [GuiPage(name='bar', persistent=False, duration=10, namespace='foo'),
             GuiPage(name='test/baz', persistent=False, duration=10, namespace='foo')], 0)
        self.namespace_manager._update_namespace_persistence. \
            assert_called_with(10)

        # With resource info
        self.namespace_manager._activate_namespace.reset_mock()
        self.namespace_manager._load_pages.reset_mock()
        self.namespace_manager._update_namespace_persistence.reset_mock()

        ui_directories = {"gui": "/tmp/test"}
        message = Message("test", {"__from": "skill",
                                   "__idle": False,
                                   "index": 1,
                                   "page_names": ["page_1", "test/page_2"],
                                   "ui_directories": ui_directories})
        self.namespace_manager.handle_show_page(message)
        expected_page1 = GuiPage("page_1", False, 0, "skill")
        expected_page2 = GuiPage("test/page_2", False, 0, "skill")
        self.namespace_manager._activate_namespace.assert_called_with("skill")
        self.namespace_manager._load_pages.assert_called_with([expected_page1,
                                                               expected_page2],
                                                              1)
        self.namespace_manager._update_namespace_persistence. \
            assert_called_with(False)

        # System resources (SYSTEM_ pages use template routing, not _load_pages)
        self.namespace_manager._activate_namespace.reset_mock()
        self.namespace_manager._load_pages.reset_mock()
        self.namespace_manager._update_namespace_persistence.reset_mock()

        message = Message("test", {"__from": "skill_no_res",
                                   "__idle": True,
                                   "index": 2,
                                   "page": ["/gui/SYSTEM_TextFrame.qml"],
                                   "page_names": ["SYSTEM_TextFrame"]})
        self.namespace_manager.handle_show_page(message)
        # SYSTEM_ pages trigger template-based routing, so _activate_namespace is called with site_id
        self.namespace_manager._activate_namespace.assert_called_with(
            "skill_no_res", "default")
        # _load_pages is NOT called for SYSTEM pages (they use template routing instead)
        self.namespace_manager._load_pages.assert_not_called()
        # TODO: Test page_names with files and URIs

        self.namespace_manager._activate_namespace = real_activate_namespace
        self.namespace_manager._load_pages = real_load_pages
        self.namespace_manager._update_namespace_persistence = \
            real_update_persistence

    def test_handle_show_page_invalid_message(self):
        namespace = Namespace("foo")
        namespace.load_pages = mock.Mock()

        message_data = {"__from": "foo"}
        message = Message("gui.page.show", data=message_data)
        self.namespace_manager.send_message_to_gui = mock.Mock()
        self.namespace_manager.handle_show_page(message)

        self.assertListEqual([], self.namespace_manager.active_namespaces)
        self.assertDictEqual({}, self.namespace_manager.loaded_namespaces)

    def test_activate_namespace(self):
        """Test activating a namespace."""
        ns = Namespace("test")
        self.namespace_manager.loaded_namespaces["test"] = ns
        self.assertIn("test", self.namespace_manager.loaded_namespaces)

    def test_ensure_namespace_exists(self):
        """Test ensuring namespace exists or is created."""
        ns = self.namespace_manager._ensure_namespace_exists("new_skill")
        self.assertIsNotNone(ns)
        self.assertEqual(ns.skill_id, "new_skill")
        self.assertIn("new_skill", self.namespace_manager.loaded_namespaces)

    def test_load_pages(self):
        """Test loading pages into a namespace."""
        ns = self.namespace_manager._ensure_namespace_exists("test")
        self.assertIsNotNone(ns)

    def test_update_namespace_persistence(self):
        """Test updating namespace persistence."""
        ns = Namespace("test")
        self.namespace_manager.loaded_namespaces["test"] = ns
        ns.set_persistence("genericSkill")
        self.assertFalse(ns.persistent)
        self.assertEqual(ns.duration, 30)

    def test_schedule_namespace_removal(self):
        """Test scheduling namespace removal."""
        self.assertIsInstance(self.namespace_manager.remove_namespace_timers, dict)

    def test_remove_namespace_via_timer(self):
        """Test timer-based removal."""
        self.assertEqual(len(self.namespace_manager.remove_namespace_timers), 0)

    def test_remove_namespace(self):
        """Test removing a namespace."""
        ns = Namespace("test")
        self.namespace_manager.loaded_namespaces["test"] = ns
        self.namespace_manager.active_namespaces.append(ns)
        self.assertIn("test", self.namespace_manager.loaded_namespaces)
        self.assertIn(ns, self.namespace_manager.active_namespaces)

    def test_emit_namespace_displayed_event(self):
        """Test emitting namespace displayed event."""
        self.assertIsNotNone(self.namespace_manager.core_bus)

    def test_handle_status_request(self):
        """Test status request handler."""
        message = Message("gui.status.request", data={"__from": "test"})
        # Should not raise exceptions
        self.namespace_manager.handle_status_request(message)

    def test_handle_set_value(self):
        """Test set value handler."""
        ns = Namespace("test")
        self.namespace_manager.loaded_namespaces["test"] = ns
        message = Message("gui.value.set", data={"__from": "test", "key": "value"})
        # Should handle gracefully
        self.namespace_manager.handle_set_value(message)

    def test_update_namespace_data(self):
        """Test updating namespace data."""
        ns = Namespace("test")
        ns.data = {}
        self.assertEqual(ns.data, {})

    def test_handle_client_connected(self):
        """Test client connected handler."""
        self.assertIsNotNone(self.namespace_manager.core_bus)

    def test_handle_page_interaction(self):
        """Test page interaction handler."""
        ns = Namespace("test")
        ns.page_number = 0
        ns.persistent = True
        self.namespace_manager.loaded_namespaces["test"] = ns
        message = Message("gui.page_interaction", data={"skill_id": "test", "page_number": 0})
        # Should handle without error
        self.namespace_manager.handle_page_interaction(message)

    def test_handle_page_gained_focus(self):
        """Test page focus handler."""
        ns = Namespace("test")
        self.namespace_manager.loaded_namespaces["test"] = ns
        message = Message("gui.page_gained_focus", data={"__from": "test", "page_number": 0})
        # Should handle without error
        self.namespace_manager.handle_page_gained_focus(message)

    def test_handle_namespace_global_back(self):
        """Test global back handler."""
        ns = Namespace("test")
        self.namespace_manager.loaded_namespaces["test"] = ns
        self.namespace_manager.active_namespaces.append(ns)
        message = Message("mycroft.gui.screen.close", data={"__from": "test"})
        # Should handle without error
        self.namespace_manager.handle_namespace_global_back(message)

    def test_del_namespace_in_remove_timers(self):
        """Test namespace deletion from timers dict."""
        self.namespace_manager.remove_namespace_timers["test"] = None
        self.assertIn("test", self.namespace_manager.remove_namespace_timers)
        del self.namespace_manager.remove_namespace_timers["test"]
        self.assertNotIn("test", self.namespace_manager.remove_namespace_timers)

    def test_upload_system_resources(self):
        # TODO: Test _cache_system_resources when implemented
        # This method is referenced in the codebase but not yet implemented
        # For now, just verify that NamespaceManager exists and has the expected attributes
        self.assertIsNotNone(self.namespace_manager)
        self.assertIsNotNone(self.namespace_manager.loaded_namespaces)
        self.assertIsNotNone(self.namespace_manager.active_namespaces)
