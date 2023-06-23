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

from ovos_bus_client.message import Message
from ovos_utils.messagebus import FakeBus
from ovos_gui.page import GuiPage
from ovos_gui.namespace import Namespace

PATCH_MODULE = "ovos_gui.namespace"


class TestNamespaceFunctions(TestCase):
    def test_validate_page_message(self):
        from ovos_gui.namespace import _validate_page_message
        # TODO

    def test_get_idle_display_config(self):
        from ovos_gui.namespace import _get_idle_display_config
        # TODO

    def test_get_active_gui_extension(self):
        from ovos_gui.namespace import _get_active_gui_extension
        # TODO


class TestNamespace(TestCase):
    def setUp(self):
        self.namespace = Namespace("foo")

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
        self.namespace.pages = [GuiPage("foo", "foo.qml", True, 0), GuiPage("bar", "bar.qml", False, 30)]
        new_pages = [GuiPage("foobar", "foobar.qml", False, 30)]
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
        self.namespace.pages = [GuiPage("foo", "foo.qml", True, 0), GuiPage("bar", "bar.qml", False, 30)]
        new_pages = [GuiPage("foo", "foo.qml", True, 0)]
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
        self.namespace.pages = ["foo", "bar", "foobar"]
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
        self.assertListEqual(["foo", "bar"], self.namespace.pages)

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
        namespace.pages = [GuiPage("bar", "bar.qml", True, 0)]
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

    def test_handle_show_page(self):
        message_data = {"__from": "foo", "__idle": 10, "page": ["bar"]}
        message = Message("gui.page.show", data=message_data)
        patch_function = PATCH_MODULE + ".send_message_to_gui"
        with mock.patch(patch_function):
            self.namespace_manager._schedule_namespace_removal = mock.Mock()
            self.namespace_manager.handle_show_page(message)

        self.assertEqual(
            "foo", self.namespace_manager.active_namespaces[0].name
        )
        self.assertTrue("foo" in self.namespace_manager.loaded_namespaces)
        namespace = self.namespace_manager.loaded_namespaces["foo"]
        self.assertListEqual(namespace.pages, namespace.pages)

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
