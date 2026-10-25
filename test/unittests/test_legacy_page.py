"""The legacy page path: non-SYSTEM_ page names reach adapters through on_legacy_page (§4.2)."""
from unittest import mock

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

from ovos_gui.namespace import NamespaceManager
from .test_gui1_service import GUI1ServiceCase, SKILL_A, SKILL_B, _ctx

DATE_TIME = "ovos-skill-date-time.openvoiceos"


class TestLegacyPage(GUI1ServiceCase):
    def test_legacy_page_reaches_hook_with_merged_data(self):
        self.set_value(DATE_TIME, time_string="10:36 AM", ampm_string="")
        self.set_value(DATE_TIME, date_string="25/10/2026", ampm_string=None)
        self.show(DATE_TIME, ["time"], __idle=None)
        self.adapter.on_legacy_page.assert_called_once_with(
            DATE_TIME, "time", {"time_string": "10:36 AM", "date_string": "25/10/2026"}, "default")
        self.adapter.dispatch_template.assert_not_called()

    def test_order_is_update_then_legacy_page_then_activate(self):
        self.set_value(DATE_TIME, time_string="10:36 AM")
        self.show(DATE_TIME, ["time"])
        calls = [c[0] for c in self.adapter.method_calls]
        self.assertEqual(calls, ["on_session_update", "on_legacy_page", "on_namespace_activated"])

    def test_only_active_entry_is_forwarded(self):
        self.show(SKILL_A, ["CurrentWeather", "HourlyForecast"], index=1)
        self.adapter.on_legacy_page.assert_called_once_with(SKILL_A, "HourlyForecast", {}, "default")

    def test_aliased_legacy_frame_still_dispatches_template(self):
        self.show(SKILL_A, ["SYSTEM_TextFrame"])
        self.adapter.dispatch_template.assert_called_once_with("SYSTEM_text", SKILL_A, {}, "default")
        self.adapter.on_legacy_page.assert_not_called()

    def test_session_routing(self):
        self.show(SKILL_A, ["Timer"], session_id="kitchen", __idle=True)
        self.adapter.on_legacy_page.assert_called_once_with(SKILL_A, "Timer", {}, "kitchen")
        self.assertEqual(self.stack("kitchen"), [SKILL_A])

    def test_clear_deactivates_and_idles(self):
        self.show(SKILL_A, ["Timer"], __idle=True)
        self.clear(SKILL_A)
        self.adapter.on_namespace_deactivated.assert_called_once_with(SKILL_A, "default")
        self.adapter.on_idle.assert_called_once_with()

    def test_legacy_namespace_stacks_with_template_namespace(self):
        self.show(SKILL_A, ["SYSTEM_text"], __idle=True)
        self.show(SKILL_B, ["CurrentWeather"], __idle=True)
        self.adapter.reset_mock()
        self.clear(SKILL_B)
        self.adapter.on_namespace_activated.assert_called_once_with(SKILL_A, "default")

    @mock.patch("ovos_gui.namespace.LOG")
    def test_warning_logged_once_per_namespace_and_page(self, log):
        for _ in range(3):
            self.show(DATE_TIME, ["time"])
        self.show(DATE_TIME, ["date"])
        warned = [c.args[0] for c in log.warning.call_args_list]
        self.assertEqual(len(warned), 2)
        self.assertIn("'time'", warned[0])
        self.assertIn("'date'", warned[1])
        log.error.assert_not_called()
        self.assertEqual(self.adapter.on_legacy_page.call_count, 4)


class TestLegacyPageIsolation(GUI1ServiceCase):
    def test_raising_adapter_does_not_break_others(self):
        broken = mock.Mock()
        broken.on_legacy_page.side_effect = RuntimeError("boom")
        healthy = mock.Mock()
        manager = NamespaceManager(FakeBus(), adapters=[broken, healthy])
        manager.handle_show_page(Message("gui.page.show",
                                         {"__from": SKILL_A, "page_names": ["time"]}, _ctx()))
        healthy.on_legacy_page.assert_called_once_with(SKILL_A, "time", {}, "default")
        broken.on_namespace_activated.assert_called_once_with(SKILL_A, "default")
        for timer in manager.get_session("default").remove_namespace_timers.values():
            timer.cancel()
