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
"""The OVOS-GUI-1 closed template vocabulary.

This module is the single source of truth for the ``SYSTEM_*`` template
vocabulary defined by the **OVOS-GUI-1** specification (§3). A render
backend styles each template once; producers may only name templates from
this closed set (§3.1).

Two recognition concerns live here:

* **The ``SYSTEM_`` prefix gate** (§3.2 / §8.3). The prefix is the
  discriminator the GUI service uses to recognise a conformant template
  intent. A page name that does not begin with ``SYSTEM_`` is *not* a
  template of this specification; the service must not dispatch it as one
  (it may still route it to a deployment-specific legacy path, §4.2).

* **Legacy ⇄ spec frame-name aliasing** (§3.1 / §8.1). Historically the
  producer (``ovos-bus-client``) emitted CamelCase frame names such as
  ``SYSTEM_TextFrame``; the spec vocabulary uses ``SYSTEM_text``. The
  service accepts **both** so the producer rename can land without
  breaking the QML render path that dispatches on the legacy names. The
  alias map is additive: every legacy name resolves to its spec template,
  and every spec/legacy name resolves to the legacy QML resource name the
  current render backends expect.
"""
from typing import Optional

#: Reserved prefix that discriminates a conformant template intent (§3.2).
SYSTEM_PREFIX = "SYSTEM_"

#: The closed GUI-1 template vocabulary (§3.4). Grows only by amendment of
#: the specification.
SYSTEM_TEMPLATES = frozenset({
    # State and feedback
    "SYSTEM_idle",
    "SYSTEM_loading",
    "SYSTEM_status",
    "SYSTEM_error",
    # Content primitives
    "SYSTEM_text",
    "SYSTEM_image",
    "SYSTEM_animated_image",
    "SYSTEM_list",
    "SYSTEM_grid",
    "SYSTEM_table",
    "SYSTEM_html",
    "SYSTEM_url",
    # Media
    "SYSTEM_audio_player",
    "SYSTEM_video_player",
    "SYSTEM_media_player",
    # Domain cards
    "SYSTEM_clock",
    "SYSTEM_timer",
    "SYSTEM_weather",
    "SYSTEM_map",
    "SYSTEM_face",
})

#: Legacy CamelCase frame names (as emitted by ``ovos-bus-client``'s GUI
#: API and shipped as QML resources) mapped to their GUI-1 spec template.
#: This lets the service accept the spec names additively — a producer may
#: emit either, and the service treats them as the same template.
LEGACY_TO_SPEC = {
    "SYSTEM_TextFrame": "SYSTEM_text",
    "SYSTEM_ImageFrame": "SYSTEM_image",
    "SYSTEM_AnimatedImageFrame": "SYSTEM_animated_image",
    "SYSTEM_HtmlFrame": "SYSTEM_html",
    "SYSTEM_UrlFrame": "SYSTEM_url",
    "SYSTEM_Status": "SYSTEM_status",
    "SYSTEM_Loading": "SYSTEM_loading",
    "SYSTEM_Face": "SYSTEM_face",
}

#: Spec template name -> legacy QML resource name. The current QML render
#: backends ship resources keyed by the legacy CamelCase names, so when a
#: producer emits a spec name we resolve it to the legacy resource so
#: rendering keeps working. Only the templates that have a shipped legacy
#: resource are mapped; spec templates without a legacy resource resolve
#: to themselves.
SPEC_TO_LEGACY = {spec: legacy for legacy, spec in LEGACY_TO_SPEC.items()}


def is_system_template(page_name: str) -> bool:
    """Whether ``page_name`` is recognised as a GUI-1 template intent.

    A page name is a template intent if it begins with the reserved
    ``SYSTEM_`` prefix (§3.2). This intentionally accepts both the spec
    vocabulary (``SYSTEM_text``) and the legacy frame names
    (``SYSTEM_TextFrame``) — both carry the prefix. A name without the
    prefix is a custom (non-spec) page and must not be dispatched as a
    template.

    @param page_name: candidate page name
    @return: True if the name is a ``SYSTEM_*`` template intent
    """
    return isinstance(page_name, str) and page_name.startswith(SYSTEM_PREFIX)


def normalize_template(page_name: str) -> str:
    """Resolve a template name to its canonical GUI-1 spec name.

    Legacy CamelCase frame names are mapped to their spec equivalent; spec
    names and unknown ``SYSTEM_*`` names pass through unchanged.

    @param page_name: a ``SYSTEM_*`` template name (spec or legacy)
    @return: the canonical spec template name where known, else the input
    """
    return LEGACY_TO_SPEC.get(page_name, page_name)


def resolve_render_name(page_name: str) -> str:
    """Resolve a template name to the resource name the render backend expects.

    The current QML render backends ship resources under the legacy
    CamelCase names. When a producer emits a spec name (``SYSTEM_text``)
    we resolve it to the legacy resource (``SYSTEM_TextFrame``) so existing
    QML keeps rendering. Legacy names and names without a legacy resource
    pass through unchanged.

    @param page_name: a ``SYSTEM_*`` template name (spec or legacy)
    @return: the render-backend resource name
    """
    return SPEC_TO_LEGACY.get(page_name, page_name)


def is_known_template(page_name: str) -> Optional[str]:
    """Return the canonical spec name if ``page_name`` is in the closed set.

    @param page_name: candidate template name (spec or legacy)
    @return: canonical spec name if it is a known GUI-1 template, else None
    """
    spec = normalize_template(page_name)
    return spec if spec in SYSTEM_TEMPLATES else None
