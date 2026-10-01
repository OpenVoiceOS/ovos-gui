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
"""Unit tests for the OVOS-GUI-1 closed template vocabulary."""
from unittest import TestCase

from ovos_gui.templates import (
    SYSTEM_PREFIX,
    SYSTEM_TEMPLATES,
    LEGACY_TO_SPEC,
    SPEC_TO_LEGACY,
    is_system_template,
    normalize_template,
    resolve_render_name,
    is_known_template,
)


class TestSystemPrefixGate(TestCase):
    """OVOS-GUI-1 §3.2/§8.3 - the SYSTEM_ prefix discriminates a template."""

    def test_spec_templates_carry_prefix(self):
        for tpl in SYSTEM_TEMPLATES:
            self.assertTrue(tpl.startswith(SYSTEM_PREFIX), tpl)
            self.assertTrue(is_system_template(tpl), tpl)

    def test_legacy_names_recognised_as_templates(self):
        for legacy in LEGACY_TO_SPEC:
            self.assertTrue(is_system_template(legacy), legacy)

    def test_non_system_names_rejected(self):
        for name in ("Weather", "skill.openvoiceos.MyPage", "custom_qml",
                     "system_text", "", "idle"):
            self.assertFalse(is_system_template(name), name)

    def test_non_string_is_not_template(self):
        self.assertFalse(is_system_template(None))
        self.assertFalse(is_system_template(123))
        self.assertFalse(is_system_template(["SYSTEM_text"]))


class TestFrameVocabulary(TestCase):
    """OVOS-GUI-1 §3.1/§8.1 - dual accept of legacy and spec frame names."""

    def test_legacy_resolves_to_spec(self):
        self.assertEqual(normalize_template("SYSTEM_TextFrame"), "SYSTEM_text")
        self.assertEqual(normalize_template("SYSTEM_Status"), "SYSTEM_status")
        self.assertEqual(normalize_template("SYSTEM_HtmlFrame"), "SYSTEM_html")

    def test_spec_name_passes_through(self):
        self.assertEqual(normalize_template("SYSTEM_text"), "SYSTEM_text")
        self.assertEqual(normalize_template("SYSTEM_weather"), "SYSTEM_weather")

    def test_unknown_system_name_passes_through(self):
        self.assertEqual(normalize_template("SYSTEM_FutureThing"),
                         "SYSTEM_FutureThing")

    def test_spec_name_resolves_to_legacy_render_resource(self):
        # producer may emit the spec name; render backends ship legacy QML
        self.assertEqual(resolve_render_name("SYSTEM_text"), "SYSTEM_TextFrame")
        self.assertEqual(resolve_render_name("SYSTEM_status"), "SYSTEM_Status")

    def test_legacy_render_resource_passes_through(self):
        self.assertEqual(resolve_render_name("SYSTEM_TextFrame"),
                         "SYSTEM_TextFrame")

    def test_alias_maps_are_inverses(self):
        for legacy, spec in LEGACY_TO_SPEC.items():
            self.assertEqual(SPEC_TO_LEGACY[spec], legacy)

    def test_every_legacy_target_is_a_known_template(self):
        for spec in LEGACY_TO_SPEC.values():
            self.assertIn(spec, SYSTEM_TEMPLATES, spec)

    def test_is_known_template(self):
        # both spec and legacy names resolve to the canonical spec name
        self.assertEqual(is_known_template("SYSTEM_text"), "SYSTEM_text")
        self.assertEqual(is_known_template("SYSTEM_TextFrame"), "SYSTEM_text")
        self.assertIsNone(is_known_template("SYSTEM_FutureThing"))
        self.assertIsNone(is_known_template("custom_page"))


class TestReservedNamesAreNotVocabulary(TestCase):
    """OVOS-GUI-1 §3.4 - SYSTEM_confirm/SYSTEM_select are RESERVED, not
    (yet) part of the closed vocabulary. Producers MUST NOT emit them, and
    the service must not recognise them as known templates. An unknown
    ``SYSTEM_*`` name is still prefix-gated (§3.2, still a template intent)
    but is not dispatchable — it is an ordinary undispatchable template,
    not an error.
    """

    def test_reserved_names_are_not_in_the_closed_vocabulary(self):
        for name in ("SYSTEM_confirm", "SYSTEM_select"):
            self.assertNotIn(name, SYSTEM_TEMPLATES, name)

    def test_reserved_names_are_unknown_templates(self):
        for name in ("SYSTEM_confirm", "SYSTEM_select"):
            self.assertIsNone(is_known_template(name), name)

    def test_reserved_names_still_carry_the_system_prefix(self):
        # unknown != not-a-template-intent; the prefix gate is separate
        # from vocabulary membership (§3.2 vs §3.4).
        for name in ("SYSTEM_confirm", "SYSTEM_select"):
            self.assertTrue(is_system_template(name), name)

    def test_legacy_input_box_alias_is_withdrawn(self):
        # SYSTEM_InputBox pointed at the now-reserved SYSTEM_confirm; the
        # alias must not exist and must not resolve to a QML resource that
        # does not ship (SYSTEM_InputBox.qml never existed).
        self.assertNotIn("SYSTEM_InputBox", LEGACY_TO_SPEC)
        self.assertNotIn("SYSTEM_InputBox", SPEC_TO_LEGACY.values())
