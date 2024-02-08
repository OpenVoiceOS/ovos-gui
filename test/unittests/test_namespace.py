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
from os import makedirs
from os.path import join, dirname, isdir, isfile
from shutil import rmtree
from unittest import TestCase, mock
from unittest.mock import Mock

from ovos_bus_client.message import Message
from ovos_utils.messagebus import FakeBus

from ovos_gui.namespace import Namespace
from ovos_gui.page import GuiPage

PATCH_MODULE = "ovos_gui.namespace"


class TestNamespaceFunctions(TestCase):
    def test_validate_page_message(self):
        pass
        # TODO

    def test_get_idle_display_config(self):
        pass
        # TODO

    def test_get_active_gui_extension(self):
        pass
        # TODO


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
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function) as send_message_mock:
            self.namespace.add()
            send_message_mock.assert_called_with(add_namespace_message)

    def test_activate(self):
        self.namespace.load_pages([
            GuiPage(name="foo", url="", persistent=False, duration=False),
            GuiPage(name="bar", url="", persistent=False, duration=False),
            GuiPage(name="foobar", url="", persistent=False, duration=False),
            GuiPage(name="baz", url="", persistent=False, duration=False),
            GuiPage(name="foobaz", url="", persistent=False, duration=False)
        ])
        activate_namespace_message = {
            "type": "mycroft.session.list.move",
            "namespace": "mycroft.system.active_skills",
            "from": 5,
            "to": 0,
            "items_number": 1
        }
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function) as send_message_mock:
            self.namespace.activate(position=5)
            send_message_mock.assert_called_with(activate_namespace_message)

    def test_remove(self):
        self.namespace.data = dict(foo="bar")
        self.namespace.pages = ["foo", "bar"]
        remove_namespace_message = dict(
            type="mycroft.session.list.remove",
            namespace="mycroft.system.active_skills",
            position=3,
            items_number=1
        )
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function) as send_message_mock:
            self.namespace.remove(position=3)
            send_message_mock.assert_called_with(remove_namespace_message)

        self.assertFalse(self.namespace.data)
        self.assertFalse(self.namespace.pages)

    def test_load_data(self):
        load_data_message = dict(
            type="mycroft.session.set",
            namespace="foo",
            data=dict(foo="bar")
        )
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function) as send_message_mock:
            self.namespace.load_data(name="foo", value="bar")
            send_message_mock.assert_called_with(load_data_message)

    def test_unload_data(self):
        # TODO
        pass

    def test_get_position_of_last_item_in_data(self):
        # TODO
        pass

    def test_set_persistence_numeric(self):
        self.namespace.set_persistence("genericSkill")
        self.assertEqual(self.namespace.duration, 30)
        self.assertFalse(self.namespace.persistent)

    def test_set_persistence_boolean(self):
        self.namespace.set_persistence("idleDisplaySkill")
        self.assertEqual(self.namespace.duration, 0)
        self.assertTrue(self.namespace.persistent)

    def test_load_pages_new(self):
        self.namespace.pages = [GuiPage(name="foo", url="foo.qml", persistent=True, duration=0),
                                GuiPage(name="bar", url="bar.qml", persistent=False, duration=30)]
        new_pages = [GuiPage(name="foobar", url="foobar.qml", persistent=False, duration=30)]
        load_page_message = dict(
            type="mycroft.events.triggered",
            namespace="foo",
            event_name="page_gained_focus",
            data=dict(number=2)
        )
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function) as send_message_mock:
            show_index = None
            self.namespace.load_pages(new_pages, show_index)
            send_message_mock.assert_called_with(load_page_message)
        self.assertListEqual(self.namespace.pages, self.namespace.pages)

    def test_load_pages_existing(self):
        self.namespace.pages = [GuiPage(name="foo", url="foo.qml", persistent=True, duration=0),
                                GuiPage(name="bar", url="bar.qml", persistent=False, duration=30)]
        new_pages = [GuiPage(name="foo", url="foo.qml", persistent=True, duration=0)]
        load_page_message = dict(
            type="mycroft.events.triggered",
            namespace="foo",
            event_name="page_gained_focus",
            data=dict(number=0)
        )
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function) as send_message_mock:
            show_index = None
            self.namespace.load_pages(new_pages, show_index)
            send_message_mock.assert_called_with(load_page_message)
        self.assertListEqual(self.namespace.pages, self.namespace.pages)

    def test_add_pages(self):
        # TODO
        pass

    def test_activate_page(self):
        # TODO
        pass

    def test_remove_pages(self):
        self.namespace.pages = [GuiPage(name="foo", url="", persistent=False, duration=False),
                                GuiPage(name="bar", url="", persistent=False, duration=False),
                                GuiPage(name="foobar", url="", persistent=False, duration=False)]
        remove_page_message = dict(
            type="mycroft.gui.list.remove",
            namespace="foo",
            position=2,
            items_number=1
        )
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function) as send_message_mock:
            self.namespace.remove_pages([2])
            send_message_mock.assert_called_with(remove_page_message)
        self.assertListEqual(["foo", "bar"], self.namespace.page_names)

    def test_page_gained_focus(self):
        # TODO
        pass

    def test_page_update_interaction(self):
        # TODO
        pass

    def test_get_page_at_position(self):
        # TODO
        pass

    def test_get_active_page(self):
        # TODO
        pass

    def test_index_in_pages_list(self):
        # TODO
        pass

    def test_global_back(self):
        # TODO
        pass


class TestNamespaceManager(TestCase):
    def setUp(self):
        from ovos_gui.namespace import NamespaceManager
        with mock.patch(PATCH_MODULE + ".create_gui_service"):
            self.namespace_manager = NamespaceManager(FakeBus())

    def test_init_gui_file_share(self):
        # TODO
        pass

    def test_handle_ready(self):
        self.assertEqual(len(self.namespace_manager.core_bus.ee.
                             listeners("gui.volunteer_page_upload")), 0)
        self.assertFalse(self.namespace_manager._ready_event.is_set())
        self.namespace_manager.handle_ready(Message(""))
        self.assertTrue(self.namespace_manager._ready_event.wait(0.01))
        self.assertEqual(len(self.namespace_manager.core_bus.ee.
                             listeners("gui.volunteer_page_upload")), 1)

    def test_handle_gui_pages_available(self):
        # TODO
        pass

    def test_handle_receive_gui_pages(self):
        # TODO
        pass

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
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function) as send_message_mock:
            self.namespace_manager.handle_send_event(message)
            send_message_mock.assert_called_with(event_triggered_message)

    def test_handle_delete_page_active_namespace(self):
        namespace = Namespace("foo")
        namespace.pages = [GuiPage(name="bar", url="bar.qml", persistent=True, duration=0)]
        namespace.remove_pages = mock.Mock()
        self.namespace_manager.loaded_namespaces = dict(foo=namespace)
        self.namespace_manager.active_namespaces = [namespace]

        message_data = {"__from": "foo", "page": ["bar"]}
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
        # TODO
        pass

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

    def test_legacy_show_page(self):
        message = Message("gui.page.show", data={"__from": "foo",
                                                 "__idle": 10,
                                                 "page": ["bar", "test/baz"]})
        pages = self.namespace_manager._legacy_show_page(message)
        self.assertEqual(pages, [GuiPage('bar', 'bar', False, 10),
                                 GuiPage('test/baz', 'baz', False, 10)])

    def test_handle_show_page(self):
        real_legacy_show_page = self.namespace_manager._legacy_show_page
        real_activate_namespace = self.namespace_manager._activate_namespace
        real_load_pages = self.namespace_manager._load_pages
        real_update_persistence = self.namespace_manager._update_namespace_persistence
        self.namespace_manager._legacy_show_page = Mock(return_value=["pages"])
        self.namespace_manager._activate_namespace = Mock()
        self.namespace_manager._load_pages = Mock()
        self.namespace_manager._update_namespace_persistence = Mock()

        # Legacy message
        message = Message("gui.page.show", data={"__from": "foo",
                                                 "__idle": 10,
                                                 "page": ["bar", "test/baz"]})
        self.namespace_manager.handle_show_page(message)
        self.namespace_manager._legacy_show_page.assert_called_once_with(message)
        self.namespace_manager._activate_namespace.assert_called_with("foo")
        self.namespace_manager._load_pages.assert_called_with(["pages"], None)
        self.namespace_manager._update_namespace_persistence. \
            assert_called_with(10)

        # With resource info
        ui_directories = {"gui": "/tmp/test"}
        message = Message("test", {"__from": "skill",
                                   "__idle": False,
                                   "index": 1,
                                   "page": ["/gui/page_1", "/gui/test/page_2"],
                                   "page_names": ["page_1", "test/page_2"],
                                   "ui_directories": ui_directories})
        self.namespace_manager.handle_show_page(message)
        expected_page1 = GuiPage(None, "page_1", False, 0, "page_1", "skill",
                                 ui_directories)
        expected_page2 = GuiPage(None, "test/page_2", False, 0, "test/page_2",
                                 "skill", ui_directories)
        self.namespace_manager._legacy_show_page.assert_called_once()
        self.namespace_manager._activate_namespace.assert_called_with("skill")
        self.namespace_manager._load_pages.assert_called_with([expected_page1,
                                                               expected_page2],
                                                              1)
        self.namespace_manager._update_namespace_persistence. \
            assert_called_with(False)

        # System resources
        message = Message("test", {"__from": "skill_no_res",
                                   "__idle": True,
                                   "index": 2,
                                   "page": ["/gui/SYSTEM_TextFrame.qml"],
                                   "page_names": ["SYSTEM_TextFrame"]})
        self.namespace_manager.handle_show_page(message)
        expected_page = GuiPage(None, "SYSTEM_TextFrame", True, 0,
                                "SYSTEM_TextFrame", "skill_no_res",
                                {"all": self.namespace_manager._system_res_dir})
        self.namespace_manager._legacy_show_page.assert_called_once()
        self.namespace_manager._activate_namespace.assert_called_with(
            "skill_no_res")
        self.namespace_manager._load_pages.assert_called_with([expected_page],
                                                              2)
        self.namespace_manager._update_namespace_persistence. \
            assert_called_with(True)
        # TODO: Test page_names with files and URIs

        self.namespace_manager._legacy_show_page = real_legacy_show_page
        self.namespace_manager._activate_namespace = real_activate_namespace
        self.namespace_manager._load_pages = real_load_pages
        self.namespace_manager._update_namespace_persistence = \
            real_update_persistence

    def test_handle_show_page_invalid_message(self):
        namespace = Namespace("foo")
        namespace.load_pages = mock.Mock()

        message_data = {"__from": "foo"}
        message = Message("gui.page.show", data=message_data)
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function):
            self.namespace_manager.handle_show_page(message)

        self.assertListEqual([], self.namespace_manager.active_namespaces)
        self.assertDictEqual({}, self.namespace_manager.loaded_namespaces)

    def test_activate_namespace(self):
        # TODO
        pass

    def test_ensure_namespace_exists(self):
        # TODO
        pass

    def test_load_pages(self):
        # TODO
        pass

    def test_update_namespace_persistence(self):
        # TODO
        pass

    def test_schedule_namespace_removal(self):
        # TODO
        pass

    def test_remove_namespace_via_timer(self):
        # TODO
        pass

    def test_remove_namespace(self):
        # TODO
        pass

    def test_emit_namespace_displayed_event(self):
        # TODO
        pass

    def test_handle_status_request(self):
        # TODO
        pass

    def test_handle_set_value(self):
        # TODO
        pass

    def test_update_namespace_data(self):
        # TODO
        pass

    def test_handle_client_connected(self):
        # TODO
        pass

    def test_handle_page_interaction(self):
        # TODO
        pass

    def test_handle_page_gained_focus(self):
        # TODO
        pass

    def test_handle_namespace_global_back(self):
        # TODO
        pass

    def test_del_namespace_in_remove_timers(self):
        # TODO
        pass

    def test_upload_system_resources(self):
        test_dir = join(dirname(__file__), "upload_test")
        makedirs(test_dir, exist_ok=True)
        self.namespace_manager.gui_file_path = test_dir
        self.namespace_manager._upload_system_resources()
        self.assertTrue(isdir(join(test_dir, "system", "qt5")))
        self.assertTrue(isfile(join(test_dir, "system", "qt5",
                                    "SYSTEM_TextFrame.qml")))
        # Test repeated copy doesn't raise any exception
        self.namespace_manager._upload_system_resources()
        self.assertTrue(isdir(join(test_dir, "system", "qt5")))
        self.assertTrue(isfile(join(test_dir, "system", "qt5",
                                    "SYSTEM_TextFrame.qml")))
        rmtree(test_dir)
