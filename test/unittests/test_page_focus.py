"""gui.page.focus: a backend asks for another held entry (GUI-1 amendment B)."""
from unittest import mock

from ovos_bus_client.message import Message

from .test_gui1_service import GUI1ServiceCase, SKILL_A, SKILL_B, _ctx


class PageFocusCase(GUI1ServiceCase):
    def focus(self, namespace, page_number, session_id="default"):
        data = {"namespace": namespace, "page_number": page_number}
        self.bus.emit(Message("gui.page.focus", data, _ctx(session_id)))

    def timer(self, skill_id, session_id="default"):
        return self.manager.get_session(session_id).remove_namespace_timers.get(skill_id)


class TestPageFocus(PageFocusCase):
    def test_focus_redispatches_the_requested_entry(self):
        self.set_value(SKILL_A, text="hi")
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], __idle=True)
        self.adapter.reset_mock()
        self.focus(SKILL_A, 1)
        self.adapter.dispatch_template.assert_called_once_with(
            "SYSTEM_image", SKILL_A, {"text": "hi"}, "default")
        self.assertEqual(self.manager.get_active_namespace().active_index, 1)

    def test_focus_does_not_reorder_or_reactivate(self):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], __idle=True)
        self.adapter.reset_mock()
        self.focus(SKILL_A, 1)
        self.adapter.on_namespace_activated.assert_not_called()
        self.assertEqual(self.stack(), [SKILL_A])

    def test_legacy_namespace_redispatches_through_legacy_hook(self):
        self.show(SKILL_A, ["CurrentWeather", "HourlyForecast"], __idle=True)
        self.adapter.reset_mock()
        self.focus(SKILL_A, 1)
        self.adapter.on_legacy_page.assert_called_once_with(SKILL_A, "HourlyForecast", {},
                                                            "default")
        self.adapter.dispatch_template.assert_not_called()

    def test_focus_on_current_entry_restarts_timer_without_dispatch(self):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], __idle=30)
        before = self.timer(SKILL_A)
        self.adapter.reset_mock()
        self.focus(SKILL_A, 0)
        self.adapter.dispatch_template.assert_not_called()
        self.assertIsNot(self.timer(SKILL_A), before)
        self.assertTrue(before.finished.is_set())

    def test_focus_is_per_session(self):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], session_id="kitchen", __idle=True)
        self.adapter.reset_mock()
        self.focus(SKILL_A, 1, session_id="kitchen")
        self.adapter.dispatch_template.assert_called_once_with(
            "SYSTEM_image", SKILL_A, {}, "kitchen")


class TestIgnoredFocus(PageFocusCase):
    def assert_ignored(self, log):
        self.adapter.dispatch_template.assert_not_called()
        self.adapter.on_legacy_page.assert_not_called()
        self.assertEqual(log.warning.call_count, 1)

    @mock.patch("ovos_gui.page_focus.LOG")
    def test_namespace_not_on_top(self, log):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], __idle=True)
        self.show(SKILL_B, ["SYSTEM_text"], __idle=True)
        self.adapter.reset_mock()
        self.focus(SKILL_A, 1)
        self.assert_ignored(log)
        self.assertIn("not on top", log.warning.call_args[0][0])

    @mock.patch("ovos_gui.page_focus.LOG")
    def test_page_number_out_of_range(self, log):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], __idle=True)
        self.adapter.reset_mock()
        self.focus(SKILL_A, 2)
        self.assert_ignored(log)
        self.assertIn("out of range", log.warning.call_args[0][0])

    @mock.patch("ovos_gui.page_focus.LOG")
    def test_other_session(self, log):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], __idle=True)
        self.adapter.reset_mock()
        self.focus(SKILL_A, 1, session_id="kitchen")
        self.assert_ignored(log)

    @mock.patch("ovos_gui.page_focus.LOG")
    def test_page_number_not_an_integer(self, log):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], __idle=True)
        self.adapter.reset_mock()
        self.focus(SKILL_A, True)
        self.assert_ignored(log)
