# Copyright 2024 OpenVoiceOS
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
"""Service-side OVOS-GUI-1 conformance tests.

Boots the real :class:`NamespaceManager` on a :class:`FakeBus` and drives
``gui.page.show`` / ``gui.value.set`` / ``gui.clear.namespace`` messages,
asserting:

* the SYSTEM_ template prefix gate (§3.2 / §4.2 / §8.3);
* legacy ⇄ spec frame-name dual-accept (§3.1 / §8.1);
* per-session namespace isolation (§4.3 / §5.1 / §8.3).
"""
from unittest import TestCase, mock

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

from ovos_gui.namespace import NamespaceManager, DEFAULT_SESSION_ID

PATCH_MODULE = "ovos_gui.namespace"


def _show(skill_id, page_names, session_id=None, idle=True, index=0):
    """Build a gui.page.show Message, optionally session-scoped."""
    data = {"__from": skill_id, "__idle": idle,
            "page_names": page_names, "index": index}
    context = {}
    if session_id is not None:
        context["session"] = {"session_id": session_id}
    return Message("gui.page.show", data=data, context=context)


def _set(skill_id, values, session_id=None):
    data = {"__from": skill_id}
    data.update(values)
    context = {}
    if session_id is not None:
        context["session"] = {"session_id": session_id}
    return Message("gui.value.set", data=data, context=context)


def _clear(skill_id, session_id=None):
    context = {}
    if session_id is not None:
        context["session"] = {"session_id": session_id}
    return Message("gui.clear.namespace", data={"__from": skill_id},
                   context=context)


class GUI1ConformanceTestCase(TestCase):
    def setUp(self):
        with mock.patch(PATCH_MODULE + ".create_gui_service"):
            self.mgr = NamespaceManager(FakeBus())


class TestSystemPrefixGate(GUI1ConformanceTestCase):
    """§3.2/§4.2/§8.3 - only SYSTEM_* page names are template intents."""

    def test_system_template_is_dispatched(self):
        self.mgr.handle_show_page(_show("weather.openvoiceos", ["SYSTEM_weather"]))
        active = self.mgr.active_namespaces
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].skill_id, "weather.openvoiceos")
        self.assertIn("SYSTEM_weather", active[0].page_names)

    def test_non_system_page_routed_to_legacy_not_template(self):
        # A custom (non-SYSTEM_) page is the legacy custom-QML path. The
        # service still tracks it (it does not crash), but it is recognised
        # as NOT a template intent.
        from ovos_gui.templates import is_system_template
        self.assertFalse(is_system_template("MyCustomPage"))
        # service must not raise on a legacy page name
        self.mgr.handle_show_page(_show("skill.test", ["MyCustomPage"]))
        # legacy page is tracked under the namespace by its raw name
        active = self.mgr.active_namespaces
        self.assertEqual(active[0].skill_id, "skill.test")
        self.assertIn("MyCustomPage", active[0].page_names)


class TestFrameVocabularyDualAccept(GUI1ConformanceTestCase):
    """§3.1/§8.1 - the service accepts both legacy and spec frame names."""

    def test_legacy_frame_name_renders_with_legacy_resource(self):
        self.mgr.handle_show_page(_show("skill.a", ["SYSTEM_TextFrame"]))
        self.assertIn("SYSTEM_TextFrame",
                      self.mgr.active_namespaces[0].page_names)

    def test_spec_frame_name_resolves_to_legacy_render_resource(self):
        # producer emits the GUI-1 spec name; service resolves it to the
        # legacy QML resource so existing render backends keep working.
        self.mgr.handle_show_page(_show("skill.b", ["SYSTEM_text"]))
        self.assertIn("SYSTEM_TextFrame",
                      self.mgr.active_namespaces[0].page_names)

    def test_spec_name_without_legacy_resource_passes_through(self):
        self.mgr.handle_show_page(_show("skill.c", ["SYSTEM_weather"]))
        self.assertIn("SYSTEM_weather",
                      self.mgr.active_namespaces[0].page_names)


class TestOptionalIdleOmission(GUI1ConformanceTestCase):
    """§3.3/§4.3 - producers may omit __idle entirely; an absent key means
    "use the namespace default", not a crash."""

    def test_absent_idle_key_does_not_raise(self):
        msg = Message("gui.page.show",
                       data={"__from": "skill.no_idle",
                             "page_names": ["SYSTEM_weather"], "index": 0},
                       context={})
        # must not raise KeyError
        self.mgr.handle_show_page(msg)
        active = self.mgr.active_namespaces
        self.assertEqual(active[0].skill_id, "skill.no_idle")
        self.assertIn("SYSTEM_weather", active[0].page_names)

    def test_absent_idle_key_uses_default_persistence(self):
        msg = Message("gui.page.show",
                       data={"__from": "skill.no_idle2",
                             "page_names": ["SYSTEM_weather"], "index": 0},
                       context={})
        self.mgr.handle_show_page(msg)
        page = self.mgr.active_namespaces[0].pages[0]
        # default behavior per _parse_persistence: not persistent, 30s
        self.assertFalse(page.persistent)
        self.assertEqual(page.duration, 30)


class TestSessionRouting(GUI1ConformanceTestCase):
    """§4.3/§5.1/§8.3 - independent namespace stack per session_id."""

    def test_absent_session_defaults_to_default(self):
        self.mgr.handle_show_page(_show("skill.a", ["SYSTEM_text"]))
        self.assertIn(DEFAULT_SESSION_ID, self.mgr.sessions)
        self.assertEqual(
            self.mgr.sessions[DEFAULT_SESSION_ID].active_namespaces[0].skill_id,
            "skill.a")

    def test_empty_session_id_defaults_to_default(self):
        msg = _show("skill.a", ["SYSTEM_text"])
        msg.context["session"] = {"session_id": ""}
        self.mgr.handle_show_page(msg)
        self.assertEqual(
            self.mgr.sessions[DEFAULT_SESSION_ID].active_namespaces[0].skill_id,
            "skill.a")

    def test_sessions_are_isolated(self):
        # two distinct sessions show different namespaces; neither collides
        self.mgr.handle_show_page(_show("skill.a", ["SYSTEM_text"],
                                        session_id="roomA"))
        self.mgr.handle_show_page(_show("skill.b", ["SYSTEM_weather"],
                                        session_id="roomB"))

        self.assertIn("roomA", self.mgr.sessions)
        self.assertIn("roomB", self.mgr.sessions)

        a = self.mgr.sessions["roomA"].active_namespaces
        b = self.mgr.sessions["roomB"].active_namespaces
        self.assertEqual([n.skill_id for n in a], ["skill.a"])
        self.assertEqual([n.skill_id for n in b], ["skill.b"])
        # the default (on-device) session was never touched
        self.assertEqual(self.mgr.sessions[DEFAULT_SESSION_ID].active_namespaces,
                         [])

    def test_value_set_is_session_scoped(self):
        self.mgr.handle_show_page(_show("weather.x", ["SYSTEM_weather"],
                                        session_id="roomA"))
        self.mgr.handle_set_value(_set("weather.x", {"current_temp": 22},
                                       session_id="roomA"))
        self.mgr.handle_set_value(_set("weather.x", {"current_temp": 5},
                                       session_id="roomB"))

        ns_a = self.mgr.sessions["roomA"].loaded_namespaces["weather.x"]
        ns_b = self.mgr.sessions["roomB"].loaded_namespaces["weather.x"]
        self.assertEqual(ns_a.data.get("current_temp"), 22)
        self.assertEqual(ns_b.data.get("current_temp"), 5)

    def test_clear_only_affects_its_session(self):
        self.mgr.handle_show_page(_show("skill.a", ["SYSTEM_text"],
                                        session_id="roomA"))
        self.mgr.handle_show_page(_show("skill.a", ["SYSTEM_text"],
                                        session_id="roomB"))
        # clear in roomA only
        self.mgr.handle_clear_namespace(_clear("skill.a", session_id="roomA"))

        # roomA's last active namespace was removed, so the (non-default)
        # session is evicted entirely rather than lingering empty.
        self.assertNotIn("roomA", self.mgr.sessions)
        self.assertEqual(
            [n.skill_id for n in self.mgr.sessions["roomB"].active_namespaces],
            ["skill.a"])

    def test_default_session_proxies(self):
        # the legacy single-screen proxies map to the "default" session
        self.mgr.handle_show_page(_show("skill.a", ["SYSTEM_text"]))
        self.assertIs(self.mgr.active_namespaces,
                      self.mgr.sessions[DEFAULT_SESSION_ID].active_namespaces)
        self.assertIs(self.mgr.loaded_namespaces,
                      self.mgr.sessions[DEFAULT_SESSION_ID].loaded_namespaces)


class TestLegacyWireGatedToDefaultSession(GUI1ConformanceTestCase):
    """§4.3/§5.1 - only the DEFAULT session drives the legacy single-screen
    wire transport (mycroft.session.list.* / mycroft.events.triggered).

    Executed proof (pair review): without this gate, a remote/non-default
    session's page show/remove emits on the ONE global
    mycroft.system.active_skills list, which is shared with the on-device
    default session - a non-default session can take over the on-device
    screen, and a non-default remove can emit a stack position that
    actually belongs to the default session's entry. This is a regression
    test for that cross-session corruption; it must FAIL before the fix
    (gate absent) and PASS after (gate present).
    """

    def test_non_default_session_emits_nothing_on_legacy_wire(self):
        with mock.patch(PATCH_MODULE + ".send_message_to_gui") as send:
            self.mgr.handle_show_page(
                _show("skill.remote", ["SYSTEM_text"], session_id="roomA"))
            self.assertEqual(
                send.call_count, 0,
                "non-default session must not emit on the legacy "
                "mycroft.session.list.* / mycroft.events.triggered wire")

    def test_default_session_still_emits_on_legacy_wire(self):
        with mock.patch(PATCH_MODULE + ".send_message_to_gui") as send:
            self.mgr.handle_show_page(_show("skill.local", ["SYSTEM_text"]))
            self.assertGreater(send.call_count, 0)

    def test_default_stack_position_unaffected_by_non_default_activity(self):
        # default session gets a namespace first
        self.mgr.handle_show_page(_show("skill.local", ["SYSTEM_text"]))
        default_stack = self.mgr.sessions[DEFAULT_SESSION_ID].active_namespaces
        self.assertEqual([n.skill_id for n in default_stack], ["skill.local"])

        # unrelated non-default session activity must not perturb it
        self.mgr.handle_show_page(
            _show("skill.remote", ["SYSTEM_text"], session_id="roomA"))
        self.mgr.handle_show_page(
            _show("skill.remote2", ["SYSTEM_weather"], session_id="roomA"))

        self.assertEqual([n.skill_id for n in default_stack], ["skill.local"])

        # removing the default namespace afterward must still reflect only
        # the default session's own stack
        self.mgr.handle_clear_namespace(_clear("skill.local"))
        self.assertEqual(default_stack, [])
        # roomA's stack is untouched by default's removal
        self.assertEqual(
            [n.skill_id for n in self.mgr.sessions["roomA"].active_namespaces],
            ["skill.remote2", "skill.remote"])


class TestSessionEviction(GUI1ConformanceTestCase):
    """A non-default session is evicted (and its timers cancelled) once
    its last active namespace is removed; the default session is never
    evicted."""

    def test_session_evicted_when_last_namespace_removed(self):
        self.mgr.handle_show_page(
            _show("skill.remote", ["SYSTEM_text"], session_id="roomA"))
        self.assertIn("roomA", self.mgr.sessions)
        session = self.mgr.sessions["roomA"]
        timer = session.remove_namespace_timers.get("skill.remote")

        self.mgr.handle_clear_namespace(_clear("skill.remote", session_id="roomA"))

        self.assertNotIn("roomA", self.mgr.sessions)
        if timer is not None:
            self.assertFalse(timer.is_alive())

    def test_session_kept_while_a_namespace_remains_active(self):
        self.mgr.handle_show_page(
            _show("skill.a", ["SYSTEM_text"], session_id="roomA"))
        self.mgr.handle_show_page(
            _show("skill.b", ["SYSTEM_weather"], session_id="roomA"))

        self.mgr.handle_clear_namespace(_clear("skill.a", session_id="roomA"))

        self.assertIn("roomA", self.mgr.sessions)
        self.assertEqual(
            [n.skill_id for n in self.mgr.sessions["roomA"].active_namespaces],
            ["skill.b"])

    def test_default_session_is_never_evicted(self):
        self.mgr.handle_show_page(_show("skill.local", ["SYSTEM_text"]))
        self.mgr.handle_clear_namespace(_clear("skill.local"))
        self.assertIn(DEFAULT_SESSION_ID, self.mgr.sessions)
