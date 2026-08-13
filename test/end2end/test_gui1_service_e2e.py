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
"""OVOS-GUI-1 in-repo end-to-end conformance.

The unit suite (``test/unittests/test_gui1_conformance.py``) calls the
:class:`~ovos_gui.namespace.NamespaceManager` handlers directly. This e2e
suite instead drives the **whole producer -> bus -> service** path with the
real components and observes the wire with ovoscope's ``GUICaptureSession``:

* the installed producer helper ``ovos_bus_client.apis.gui.GUIInterface``
  emits ``gui.value.set`` / ``gui.page.show`` / ``gui.clear.namespace`` on a
  real bus (the on-device ``"default"`` session);
* the real ``NamespaceManager`` (its websocket render service mocked out, as
  there is no QML backend in CI) consumes those Messages off the same bus and
  drives the namespace lifecycle, emitting ``gui.namespace.*`` back on the
  core bus;
* ovoscope captures the ``gui.*`` traffic and the assertions check the
  GUI-1 bus contract end to end.

Clauses asserted (OVOS-GUI-1, ``ovos/org/architecture/gui-1.md``):

* §2.3   producer emits its §4 wire protocol with no render backend attached;
* §3.1/§8.1  the service dual-accepts the legacy (``SYSTEM_TextFrame``) and
  spec (``SYSTEM_text``) frame vocabulary;
* §3.2/§4.2/§8.3  the ``SYSTEM_`` prefix gates a template intent; a non-
  ``SYSTEM_`` first page is routed to the legacy path, not dispatched as a
  template;
* §4.1   ``__from`` rides every GUI Message and the reserved keys are protocol
  metadata, never namespace session data;
* §4.3   the namespace lifecycle — activate on ``gui.page.show``, remove on
  ``gui.clear.namespace`` (observable as ``gui.namespace.removed`` on the
  core bus);
* §4.3/§5.1/§8.3  each ``session_id`` owns an independent namespace stack and
  an absent session defaults to the reserved ``"default"``.
"""
import time
from unittest import TestCase, mock

from ovos_bus_client.apis.gui import GUIInterface
from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

from ovoscope import GUICaptureSession

# The render service binds a websocket on construction; there is no QML backend
# in CI, so stub it. Everything else (handlers, namespace stacks, core-bus
# emissions) is the real NamespaceManager.
_PATCH_GUI_SERVICE = "ovos_gui.namespace.create_gui_service"

GUI_PAGE_SHOW = "gui.page.show"
GUI_VALUE_SET = "gui.value.set"
GUI_CLEAR = "gui.clear.namespace"


def _show(skill_id, page_names, session_id=None, idle=True, index=0):
    """A ``gui.page.show`` Message, optionally scoped to a ``session_id``."""
    data = {"__from": skill_id, "__idle": idle,
            "page_names": page_names, "index": index}
    context = {}
    if session_id is not None:
        context["session"] = {"session_id": session_id}
    return Message(GUI_PAGE_SHOW, data=data, context=context)


def _clear(skill_id, session_id=None):
    context = {}
    if session_id is not None:
        context["session"] = {"session_id": session_id}
    return Message(GUI_CLEAR, data={"__from": skill_id}, context=context)


class GUI1ServiceE2E(TestCase):
    """Boot the real NamespaceManager on a real bus once per test."""

    def setUp(self):
        self.bus = FakeBus()
        with mock.patch(_PATCH_GUI_SERVICE):
            from ovos_gui.namespace import NamespaceManager, DEFAULT_SESSION_ID
            self.mgr = NamespaceManager(self.bus)
        self.DEFAULT_SESSION_ID = DEFAULT_SESSION_ID

    def tearDown(self):
        # `__idle=True` schedules a deployment-default auto-removal Timer per
        # namespace; cancel them so no background thread fires after the test
        # process tears down its streams.
        for session in self.mgr.sessions.values():
            for timer in session.remove_namespace_timers.values():
                timer.cancel()

    def _settle(self):
        # let the bus deliver and the synchronous handlers run
        time.sleep(0.2)


class TestProducerWireRoundTrip(GUI1ServiceE2E):
    """§2.3/§4.1/§4.2 - the real producer's wire protocol reaches the real
    service over the bus, and the service activates the producing namespace."""

    def test_producer_drives_service_over_the_bus(self):
        """§2.3/§4.2: the installed ``GUIInterface`` producer emits
        ``gui.value.set`` then ``gui.page.show`` on the bus (no render backend
        attached), and the service consumes them and activates the namespace."""
        gui = GUIInterface("weather.openvoiceos", bus=self.bus)
        with GUICaptureSession(self.bus) as cap:
            gui["current_temp"] = 22
            gui.show_text("It is sunny", "Weather")
            self._settle()
            # §4.2 both wire Messages were emitted by the producer
            self.assertIn(GUI_VALUE_SET, [m.msg_type for m in cap.messages])
            self.assertIn(GUI_PAGE_SHOW, [m.msg_type for m in cap.messages])

        # §4.3: the service activated the producing namespace on the default
        # (on-device) session
        active = self.mgr.active_namespaces
        self.assertEqual([n.skill_id for n in active], ["weather.openvoiceos"])
        # §4.1: __from selected the namespace; the content key is session data
        ns = self.mgr.loaded_namespaces["weather.openvoiceos"]
        self.assertEqual(ns.data.get("current_temp"), 22)

    def test_every_producer_message_carries_from(self):
        """§4.1 MUST: every GUI Message the producer puts on the wire carries
        ``__from`` naming the producing namespace. Scoped to the producer's
        own wire topics: the service's ``gui.namespace.*`` announcements are
        core-bus events, not producer messages, and carry no ``__from``."""
        producer_topics = {GUI_VALUE_SET, GUI_PAGE_SHOW, GUI_CLEAR}
        gui = GUIInterface("skill.under.test", bus=self.bus)
        with GUICaptureSession(self.bus) as cap:
            gui["k"] = "v"
            gui.show_text("hi", "T")
            gui.clear()
            self._settle()
            wire = [m for m in cap.messages
                    if m.msg_type in producer_topics]
            # all three producer wire topics were emitted
            self.assertEqual({m.msg_type for m in wire}, producer_topics)
            for m in wire:
                self.assertEqual(m.data.get("__from"), "skill.under.test",
                                 f"{m.msg_type} missing/!= __from")

    def test_reserved_keys_are_not_namespace_session_data(self):
        """§4.1 MUST: the reserved ``__``-prefixed keys are protocol metadata,
        not session data — they never land in the namespace's content map."""
        gui = GUIInterface("skill.reserved", bus=self.bus)
        gui["temperature"] = 19
        gui.show_text("hi", "T")
        self._settle()
        ns = self.mgr.loaded_namespaces["skill.reserved"]
        self.assertIn("temperature", ns.data)
        self.assertNotIn("__from", ns.data)
        self.assertNotIn("__idle", ns.data)


class TestSystemPrefixGate(GUI1ServiceE2E):
    """§3.2/§4.2/§8.3 - the ``SYSTEM_`` prefix discriminates a template intent."""

    def test_system_template_dispatched(self):
        """§4.2: a ``gui.page.show`` whose first page is a ``SYSTEM_*`` template
        is dispatched and activates the namespace."""
        self.mgr.core_bus.emit(_show("weather.sk", ["SYSTEM_weather"]))
        self._settle()
        active = self.mgr.active_namespaces
        self.assertEqual([n.skill_id for n in active], ["weather.sk"])
        self.assertIn("SYSTEM_weather", active[0].page_names)

    def test_non_system_first_page_is_legacy_not_template(self):
        """§3.2/§4.2 - a non-``SYSTEM_`` first page is not a template of this
        spec. The service does not raise and recognises it as a non-template
        (legacy custom-QML) page, tracked under its raw name."""
        from ovos_gui.templates import is_system_template
        self.assertFalse(is_system_template("MyCustomPage"))
        self.mgr.core_bus.emit(_show("legacy.skill", ["MyCustomPage"]))
        self._settle()
        active = self.mgr.active_namespaces
        self.assertEqual([n.skill_id for n in active], ["legacy.skill"])
        self.assertIn("MyCustomPage", active[0].page_names)


class TestFrameVocabularyDualAccept(GUI1ServiceE2E):
    """§3.1/§8.1 - the service accepts both legacy and spec frame names."""

    def test_legacy_frame_name_accepted(self):
        """§8.1 - a producer emitting the legacy ``SYSTEM_TextFrame`` renders
        with the legacy resource (the QML backends ship it under that name)."""
        self.mgr.core_bus.emit(_show("skill.legacy", ["SYSTEM_TextFrame"]))
        self._settle()
        self.assertIn("SYSTEM_TextFrame",
                      self.mgr.active_namespaces[0].page_names)

    def test_spec_name_resolves_to_legacy_render_resource(self):
        """§3.1/§8.1 - a producer emitting the spec ``SYSTEM_text`` is accepted;
        the service resolves it to the legacy QML resource so existing render
        backends keep working."""
        self.mgr.core_bus.emit(_show("skill.spec", ["SYSTEM_text"]))
        self._settle()
        self.assertIn("SYSTEM_TextFrame",
                      self.mgr.active_namespaces[0].page_names)

    def test_real_producer_emits_legacy_and_service_accepts(self):
        """§3.1/§8.1 end-to-end: the installed ``GUIInterface.show_text``
        emits the legacy ``SYSTEM_TextFrame`` on the wire and the service
        dispatches it (the producer/service dual-accept handshake)."""
        gui = GUIInterface("weather.openvoiceos", bus=self.bus)
        with GUICaptureSession(self.bus) as cap:
            gui.show_text("hi", "T")
            self._settle()
            page = next(m for m in cap.messages if m.msg_type == GUI_PAGE_SHOW)
            self.assertTrue(page.data["page_names"][0].startswith("SYSTEM_"))
        self.assertIn("weather.openvoiceos",
                      list(self.mgr.loaded_namespaces.keys()))


class TestPerSessionRouting(GUI1ServiceE2E):
    """§4.3/§5.1/§8.3 - an independent namespace stack per ``session_id``."""

    def test_absent_session_defaults_to_default(self):
        """§5.1: an absent ``session`` routes to the reserved ``"default"``."""
        self.mgr.core_bus.emit(_show("skill.a", ["SYSTEM_text"]))
        self._settle()
        self.assertIn(self.DEFAULT_SESSION_ID, self.mgr.sessions)
        self.assertEqual(
            [n.skill_id for n in
             self.mgr.sessions[self.DEFAULT_SESSION_ID].active_namespaces],
            ["skill.a"])

    def test_two_sessions_are_isolated(self):
        """§4.3/§5.1/§8.3 MUST: a namespace shown in session A does not appear
        on session B's stack, nor on the on-device ``"default"`` stack."""
        self.mgr.core_bus.emit(_show("skill.a", ["SYSTEM_text"],
                                     session_id="roomA"))
        self.mgr.core_bus.emit(_show("skill.b", ["SYSTEM_weather"],
                                     session_id="roomB"))
        self._settle()
        self.assertEqual(
            [n.skill_id for n in self.mgr.sessions["roomA"].active_namespaces],
            ["skill.a"])
        self.assertEqual(
            [n.skill_id for n in self.mgr.sessions["roomB"].active_namespaces],
            ["skill.b"])
        # the on-device (default) session was never touched
        self.assertEqual(
            self.mgr.sessions[self.DEFAULT_SESSION_ID].active_namespaces, [])

    def test_clear_only_affects_its_session(self):
        """§4.3/§5.1: clearing a namespace in one session leaves the same
        namespace active in another session."""
        self.mgr.core_bus.emit(_show("skill.a", ["SYSTEM_text"],
                                     session_id="roomA"))
        self.mgr.core_bus.emit(_show("skill.a", ["SYSTEM_text"],
                                     session_id="roomB"))
        self._settle()
        self.mgr.core_bus.emit(_clear("skill.a", session_id="roomA"))
        self._settle()
        # roomA's last active namespace was removed, so the (non-default)
        # session is evicted entirely rather than lingering empty.
        self.assertNotIn("roomA", self.mgr.sessions)
        self.assertEqual(
            [n.skill_id for n in self.mgr.sessions["roomB"].active_namespaces],
            ["skill.a"])


class TestNamespaceLifecycle(GUI1ServiceE2E):
    """§4.3 - activate on show, remove on clear, observable on the core bus."""

    def test_clear_emits_namespace_removed_on_core_bus(self):
        """§4.3: ``gui.clear.namespace`` removes the namespace from the active
        stack and the service announces it as ``gui.namespace.removed`` on the
        core bus."""
        recs = []
        self.mgr.core_bus.on(
            "message",
            lambda m: recs.append(
                Message.deserialize(m) if isinstance(m, str) else m))
        self.mgr.core_bus.emit(_show("sk.clearme", ["SYSTEM_text"]))
        self._settle()
        self.mgr.core_bus.emit(_clear("sk.clearme"))
        self._settle()
        self.assertIn("gui.namespace.removed",
                      [m.msg_type for m in recs])
        self.assertEqual(self.mgr.active_namespaces, [])
