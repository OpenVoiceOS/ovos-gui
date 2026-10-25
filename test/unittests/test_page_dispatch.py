"""Template events carry index and page_count (GUI-1 6.3, amendment B)."""
from unittest import TestCase, mock

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

from ovos_gui.namespace import NamespaceManager
from ovos_gui.page_dispatch import accepts_entry
from .test_gui1_service import GUI1ServiceCase, SKILL_A, _ctx


class OldAdapter:
    """Hooks written before index and page_count existed."""

    def __init__(self):
        self.calls = []

    def dispatch_template(self, template, skill_id, data, session_id="default"):
        self.calls.append(("dispatch_template", template, skill_id, data, session_id))

    def on_legacy_page(self, skill_id, page, data, session_id="default"):
        self.calls.append(("on_legacy_page", skill_id, page, data, session_id))


class KwargsAdapter:
    def __init__(self):
        self.kwargs = []

    def dispatch_template(self, template, skill_id, data, session_id="default", **kwargs):
        self.kwargs.append(kwargs)


class TestEntryOnDispatch(GUI1ServiceCase):
    def test_template_show_carries_active_entry(self):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image", "SYSTEM_status"], index=2)
        self.adapter.dispatch_template.assert_called_once_with(
            "SYSTEM_status", SKILL_A, {}, "default", index=2, page_count=3)

    def test_clamped_index_is_the_one_sent(self):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], index=9)
        self.adapter.dispatch_template.assert_called_once_with(
            "SYSTEM_image", SKILL_A, {}, "default", index=1, page_count=2)

    def test_legacy_page_carries_active_entry(self):
        self.show(SKILL_A, ["time"])
        self.adapter.on_legacy_page.assert_called_once_with(
            SKILL_A, "time", {}, "default", index=0, page_count=1)

    def test_focus_redispatch_reports_new_index(self):
        self.show(SKILL_A, ["SYSTEM_text", "SYSTEM_image"], __idle=True)
        self.adapter.reset_mock()
        self.bus.emit(Message("gui.page.focus", {"namespace": SKILL_A, "page_number": 1}, _ctx()))
        self.adapter.dispatch_template.assert_called_once_with(
            "SYSTEM_image", SKILL_A, {}, "default", index=1, page_count=2)


class TestOldAdapterSignature(TestCase):
    def show(self, adapters, pages):
        manager = NamespaceManager(FakeBus(), adapters=adapters)
        manager.handle_show_page(Message("gui.page.show",
                                         {"__from": SKILL_A, "page_names": pages, "__idle": True},
                                         _ctx()))
        for timer in manager.get_session("default").remove_namespace_timers.values():
            timer.cancel()

    def test_old_template_hook_still_called(self):
        old, new = OldAdapter(), mock.Mock()
        self.show([old, new], ["SYSTEM_text", "SYSTEM_image"])
        self.assertEqual(old.calls, [("dispatch_template", "SYSTEM_text", SKILL_A, {}, "default")])
        new.dispatch_template.assert_called_once_with(
            "SYSTEM_text", SKILL_A, {}, "default", index=0, page_count=2)

    def test_old_legacy_hook_still_called(self):
        old = OldAdapter()
        self.show([old], ["time"])
        self.assertEqual(old.calls, [("on_legacy_page", SKILL_A, "time", {}, "default")])

    def test_kwargs_hook_gets_both(self):
        adapter = KwargsAdapter()
        self.show([adapter], ["SYSTEM_text"])
        self.assertEqual(adapter.kwargs, [{"index": 0, "page_count": 1}])

    @mock.patch("ovos_gui.page_dispatch.LOG")
    def test_old_hook_reported_once(self, log):
        class OnceAdapter(OldAdapter):
            pass
        self.show([OnceAdapter()], ["SYSTEM_text"])
        self.show([OnceAdapter()], ["SYSTEM_text"])
        self.assertEqual(log.info.call_count, 1)
        self.assertIn("OnceAdapter.dispatch_template", log.info.call_args[0][0])


class TestAcceptsEntry(TestCase):
    def test_signatures(self):
        self.assertTrue(accepts_entry(lambda t, s, d, session_id, index=0, page_count=1: None))
        self.assertTrue(accepts_entry(lambda *args, **kwargs: None))
        self.assertFalse(accepts_entry(lambda t, s, d, session_id="default": None))
        self.assertFalse(accepts_entry(lambda t, s, d, session_id, index=0: None))

    @mock.patch("ovos_gui.page_dispatch.inspect.signature", side_effect=ValueError)
    def test_uninspectable_callable_is_old(self, _signature):
        self.assertFalse(accepts_entry(print))
