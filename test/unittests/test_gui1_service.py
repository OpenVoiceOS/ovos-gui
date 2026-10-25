"""OVOS-GUI-1 hub behaviour, driven through the bus handlers with a recording adapter."""
import threading
from unittest import TestCase, mock

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

from ovos_gui.gui1 import STATUS_TOPICS, active_template
from ovos_gui.namespace import NamespaceManager

SKILL_A = "skill-a.test"
SKILL_B = "skill-b.test"


def _ctx(session_id="default"):
    return {"session": {"session_id": session_id}}


class GUI1ServiceCase(TestCase):
    def setUp(self):
        self.bus = FakeBus()
        self.adapter = mock.Mock()
        self.manager = NamespaceManager(self.bus, adapters=[self.adapter])

    def tearDown(self):
        for session in self.manager.sessions.values():
            for timer in list(session.remove_namespace_timers.values()):
                timer.cancel()

    def set_value(self, skill_id, session_id="default", **data):
        self.bus.emit(Message("gui.value.set", {"__from": skill_id, **data}, _ctx(session_id)))

    def show(self, skill_id, pages, session_id="default", **extra):
        data = {"__from": skill_id, "page_names": pages, **extra}
        self.bus.emit(Message("gui.page.show", data, _ctx(session_id)))

    def clear(self, skill_id, session_id="default"):
        self.bus.emit(Message("gui.clear.namespace", {"__from": skill_id}, _ctx(session_id)))

    def stack(self, session_id="default"):
        return [n.skill_id for n in self.manager.get_session(session_id).active_namespaces]


class TestSessionData(GUI1ServiceCase):
    def test_session_update_carries_merged_map(self):
        self.set_value(SKILL_A, title="Hi")
        self.set_value(SKILL_A, text="Hello")
        self.adapter.on_session_update.assert_called_with(
            SKILL_A, {"title": "Hi", "text": "Hello"}, "default")

    def test_null_removes_key(self):
        self.set_value(SKILL_A, title="Hi", text="Hello")
        self.set_value(SKILL_A, title=None)
        self.adapter.on_session_update.assert_called_with(SKILL_A, {"text": "Hello"}, "default")
        self.assertEqual(self.manager.get_namespace_data(SKILL_A), {"text": "Hello"})

    def test_reserved_keys_never_reach_adapters(self):
        self.set_value(SKILL_A, __animations=True, text="Hello")
        self.adapter.on_session_update.assert_called_with(SKILL_A, {"text": "Hello"}, "default")

    def test_template_event_carries_merged_data(self):
        self.set_value(SKILL_A, title="Hi")
        self.set_value(SKILL_A, text="Hello", title=None)
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.adapter.dispatch_template.assert_called_once_with(
            "SYSTEM_text", SKILL_A, {"text": "Hello"}, "default")


class TestShowPage(GUI1ServiceCase):
    def test_absent_idle_uses_default(self):
        self.show(SKILL_A, ["SYSTEM_text"])
        top = self.manager.get_active_namespace()
        self.assertEqual((top.persistent, top.duration), (False, 30))

    def test_idle_true_persists_without_timer(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        session = self.manager.get_session("default")
        self.assertTrue(session.active_namespaces[0].persistent)
        self.assertNotIn(SKILL_A, session.remove_namespace_timers)

    def test_new_idle_replaces_pending_timer(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=30)
        self.show(SKILL_A, ["SYSTEM_text"], __idle=5)
        timer = self.manager.get_session("default").remove_namespace_timers[SKILL_A]
        self.assertEqual(timer.interval, 5)

    def test_legacy_frame_name_dispatched_as_spec_name(self):
        self.show(SKILL_A, ["SYSTEM_TextFrame"], __idle=None)
        self.adapter.dispatch_template.assert_called_once_with("SYSTEM_text", SKILL_A, {}, "default")

    def test_only_active_entry_is_dispatched(self):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], index=1)
        self.adapter.dispatch_template.assert_called_once_with("SYSTEM_image", SKILL_A, {}, "default")

    def test_index_is_clamped(self):
        self.assertEqual(active_template(["SYSTEM_text", "SYSTEM_image"], 9), "SYSTEM_image")
        self.assertEqual(active_template(["SYSTEM_text"], None), "SYSTEM_text")

    @mock.patch("ovos_gui.gui1.LOG")
    def test_unknown_system_name_is_diagnosed_and_dispatched(self, log):
        self.show(SKILL_A, ["SYSTEM_hologram"])
        self.assertIn("SYSTEM_hologram", log.warning.call_args[0][0])
        self.adapter.dispatch_template.assert_called_once()

    @mock.patch("ovos_gui.gui1.LOG")
    def test_interactive_companions_dispatch_without_diagnostic(self, log):
        for name in ("SYSTEM_confirm", "SYSTEM_select", "SYSTEM_input"):
            self.show(SKILL_A, [name], __idle=True)
            self.adapter.dispatch_template.assert_called_with(name, SKILL_A, {}, "default")
        log.warning.assert_not_called()

    def test_activation_order_is_dispatch_then_activate(self):
        self.show(SKILL_A, ["SYSTEM_text"])
        calls = [c[0] for c in self.adapter.method_calls]
        self.assertLess(calls.index("dispatch_template"), calls.index("on_namespace_activated"))


class TestIdle(GUI1ServiceCase):
    def test_on_idle_when_last_namespace_cleared(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.clear(SKILL_A)
        self.adapter.on_namespace_deactivated.assert_called_once_with(SKILL_A, "default")
        self.adapter.on_idle.assert_called_once_with("default")

    def test_no_idle_while_stack_not_empty(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.show(SKILL_B, ["SYSTEM_text"], __idle=True)
        self.clear(SKILL_B)
        self.assertEqual(self.stack(), [SKILL_A])
        self.adapter.on_idle.assert_not_called()

    def test_exposed_namespace_is_reactivated(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.show(SKILL_B, ["SYSTEM_text"], __idle=True)
        self.adapter.reset_mock()
        self.clear(SKILL_B)
        self.adapter.on_namespace_activated.assert_called_once_with(SKILL_A, "default")

    def test_removing_lower_namespace_does_not_reactivate_top(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.show(SKILL_B, ["SYSTEM_text"], __idle=True)
        self.adapter.reset_mock()
        self.clear(SKILL_A)
        self.adapter.on_namespace_activated.assert_not_called()

    def test_on_idle_after_timer_expiry(self):
        fired = threading.Event()
        self.adapter.on_idle.side_effect = lambda session_id: fired.set()
        self.show(SKILL_A, ["SYSTEM_text"], __idle=1)
        self.assertTrue(fired.wait(3))
        self.assertEqual(self.stack(), [])
        self.adapter.on_idle.assert_called_once_with("default")

    def test_idle_names_only_the_session_that_emptied(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.show(SKILL_B, ["SYSTEM_text"], session_id="kitchen", __idle=True)
        self.clear(SKILL_B, session_id="kitchen")
        self.adapter.on_idle.assert_called_once_with("kitchen")
        self.assertEqual(self.stack(), [SKILL_A])


class TestScreenClose(GUI1ServiceCase):
    def test_release_removes_only_its_own_namespace(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.show(SKILL_B, ["SYSTEM_text"], __idle=True)
        self.clear(SKILL_B)
        self.bus.emit(Message("mycroft.gui.screen.close", {"skill_id": SKILL_B}, _ctx()))
        self.assertEqual(self.stack(), [SKILL_A])

    def test_back_without_skill_id_removes_top(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.show(SKILL_B, ["SYSTEM_text"], __idle=True)
        self.bus.emit(Message("mycroft.gui.screen.close", {}, _ctx()))
        self.assertEqual(self.stack(), [SKILL_A])


class TestSessions(GUI1ServiceCase):
    def test_stacks_are_per_session(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.show(SKILL_B, ["SYSTEM_text"], session_id="kitchen", __idle=True)
        self.assertEqual(self.stack(), [SKILL_A])
        self.assertEqual(self.stack("kitchen"), [SKILL_B])
        self.adapter.on_namespace_activated.assert_called_with(SKILL_B, "kitchen")


class TestStatusEvents(GUI1ServiceCase):
    def test_every_spec_topic_is_forwarded(self):
        for topic in STATUS_TOPICS:
            self.bus.emit(Message(topic, {"t": topic}))
        forwarded = [c.args[0] for c in self.adapter.on_status_event.call_args_list]
        self.assertEqual(forwarded, list(STATUS_TOPICS))

    def test_ambient_is_kept_and_forwarded(self):
        self.bus.emit(Message("gui.ambient.notifications", {"count": 2}))
        self.adapter.on_status_event.assert_called_once_with(
            "gui.ambient.notifications", {"count": 2}, "default")
        self.assertEqual(self.manager.get_ambient("gui.ambient.notifications"), {"count": 2})
