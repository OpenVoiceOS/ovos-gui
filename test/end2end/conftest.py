# Copyright 2026 OpenVoiceOS Contributors
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
"""Pytest fixtures for E2E adapter integration tests.

These tests use a *concrete* adapter that subclasses ``AbstractGUIPlugin``
rather than ``unittest.mock.Mock``. A Mock accepts any call signature, so it
hides arity drift between ovos-gui and the published adapter contract. The
recording adapter below enforces the real handler/hook signatures, so a routing
or contract regression fails the test instead of passing silently.
"""
from typing import List

import pytest
from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus
from ovos_plugin_manager.templates.gui import AbstractGUIPlugin

from ovos_gui.namespace import NamespaceManager


class RecordingGUIPlugin(AbstractGUIPlugin):
    """Spec-conformant adapter that records every call it receives.

    Subclassing ``AbstractGUIPlugin`` binds the template handlers and lifecycle
    hooks with their real signatures (session_id only). Calling them with the
    wrong arity raises ``TypeError`` instead of being silently accepted, which
    is exactly what we want the tests to catch.
    """

    def __init__(self, config=None, bus=None):
        super().__init__(config or {}, bus)
        # list of (kind, *payload) tuples
        self.calls: List[tuple] = []
        self._connected = True

    # --- template handlers (override a representative subset) ---------------
    def handle_show_weather(self, skill_id, data, session_id="default"):
        self.calls.append(("weather", skill_id, dict(data), session_id))

    def handle_show_text(self, skill_id, data, session_id="default"):
        self.calls.append(("text", skill_id, dict(data), session_id))

    def handle_show_clock(self, skill_id, data, session_id="default"):
        self.calls.append(("clock", skill_id, dict(data), session_id))

    # --- lifecycle hooks ----------------------------------------------------
    def on_namespace_activated(self, skill_id, session_id="default"):
        self.calls.append(("activated", skill_id, session_id))

    def on_namespace_deactivated(self, skill_id, session_id="default"):
        self.calls.append(("deactivated", skill_id, session_id))

    def on_session_update(self, skill_id, data, session_id="default"):
        self.calls.append(("session_update", skill_id, dict(data), session_id))

    def on_status_event(self, event_name, data, session_id="default"):
        self.calls.append(("status", event_name, dict(data), session_id))

    def any_client_connected(self) -> bool:
        return self._connected

    # --- helpers for assertions --------------------------------------------
    def calls_of(self, kind: str) -> List[tuple]:
        return [c for c in self.calls if c[0] == kind]


class ExplodingGUIPlugin(RecordingGUIPlugin):
    """Adapter whose hooks raise — used to verify failure isolation."""

    def on_namespace_activated(self, skill_id, session_id="default"):
        raise RuntimeError("boom")

    def dispatch_template(self, template, skill_id, data, session_id="default"):
        raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def _cancel_pending_timers():
    """Cancel namespace auto-removal timers after each test.

    Tests show non-persistent namespaces which schedule a background removal
    Timer; cancelling them keeps logs clean and avoids dangling threads.
    """
    import gc
    yield
    for obj in gc.get_objects():
        if isinstance(obj, NamespaceManager):
            for session in obj.sessions.values():
                for timer in session.remove_namespace_timers.values():
                    timer.cancel()


@pytest.fixture
def fake_bus():
    return FakeBus()


@pytest.fixture
def recording_adapter():
    return RecordingGUIPlugin()


@pytest.fixture
def second_adapter():
    return RecordingGUIPlugin()


@pytest.fixture
def manager(fake_bus, recording_adapter):
    """NamespaceManager with a single concrete recording adapter."""
    return NamespaceManager(fake_bus, adapters=[recording_adapter])


@pytest.fixture
def message_factory():
    """Factory for GUI bus messages keyed solely by session_id."""

    def page_show(page_names: List[str], skill_id: str,
                  session_id: str = "default", persistent: bool = False) -> Message:
        return Message("gui.page.show", data={
            "page_names": page_names,
            "__from": skill_id,
            "__idle": persistent,
            "index": 0,
        }, context={"session": {"session_id": session_id}})

    def set_value(namespace: str, key: str, value,
                  session_id: str = "default") -> Message:
        return Message("gui.value.set", data={
            "__from": namespace,
            key: value,
        }, context={"session": {"session_id": session_id}})

    def clear_namespace(namespace: str, session_id: str = "default") -> Message:
        return Message("gui.clear.namespace", data={
            "__from": namespace,
        }, context={"session": {"session_id": session_id}})

    return {
        "page_show": page_show,
        "set_value": set_value,
        "clear_namespace": clear_namespace,
    }
