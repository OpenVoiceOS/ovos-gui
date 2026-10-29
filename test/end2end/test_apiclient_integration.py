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
"""Full-path integration: skill-side GUIInterface -> ovos-gui -> adapter.

The other end2end tests hand-build ``gui.page.show`` / ``gui.value.set``
messages. This module instead drives a *real* :class:`GUIInterface` from the
standalone ``ovos-gui-api-client`` package, so the wire format the skill side
actually emits is proven to match what ``NamespaceManager`` parses and dispatches
to adapters. If the two packages ever drift, these tests fail.
"""
import pytest

# ovos-gui-api-client is a required test dependency (declared in the `test`
# extra and git-installed in CI) — imported directly, never skipped, so a real
# wire-format regression always fails the suite.
from ovos_gui_api_client import GUIInterface

SKILL_ID = "integration.test.skill"


@pytest.fixture
def gui(fake_bus):
    """A real skill-side GUIInterface bound to the shared FakeBus."""
    return GUIInterface(SKILL_ID, bus=fake_bus)


def test_show_weather_reaches_adapter(manager, recording_adapter, gui):
    # a skill calling the typed template method...
    gui.show_weather(current_temp=22, min_temp=15, max_temp=25, condition="Sunny", location="Lisbon")
    # ...reaches the adapter's matching handler via ovos-gui dispatch
    weather = recording_adapter.calls_of("weather")
    assert weather, f"adapter never received weather; calls={recording_adapter.calls}"
    _, skill_id, data, session_id = weather[-1]
    assert skill_id == SKILL_ID
    assert session_id == "default"
    # the session data the skill set is carried through to the adapter
    assert data.get("current_temp") == 22
    assert data.get("condition") == "Sunny"


def test_show_text_reaches_adapter(manager, recording_adapter, gui):
    gui.show_text("hello world", title="greeting")
    text = recording_adapter.calls_of("text")
    assert text, f"adapter never received text; calls={recording_adapter.calls}"
    _, skill_id, data, session_id = text[-1]
    assert skill_id == SKILL_ID
    assert "hello world" in str(data.values())


def test_fanout_from_real_interface(fake_bus, recording_adapter, second_adapter, gui):
    # both installed adapters receive the template a single skill call produced
    from ovos_gui.namespace import NamespaceManager
    NamespaceManager(fake_bus, adapters=[recording_adapter, second_adapter])
    gui.show_weather(current_temp=15, min_temp=10, max_temp=18, condition="Cloudy")
    assert recording_adapter.calls_of("weather")
    assert second_adapter.calls_of("weather")
