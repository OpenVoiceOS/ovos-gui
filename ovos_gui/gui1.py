"""OVOS-GUI-1 vocabulary the GUI service enforces.

Template catalogue (§3.4), legacy frame-name aliases for producers that
predate the rename, active-template selection (§4.2) and the status-event
topic table (§5.3).
"""
from typing import Dict, List, Optional, Tuple

from ovos_utils.log import LOG

SYSTEM_PREFIX = "SYSTEM_"

SPEC_TEMPLATES = frozenset({
    "SYSTEM_idle", "SYSTEM_loading", "SYSTEM_status", "SYSTEM_error",
    "SYSTEM_text", "SYSTEM_image", "SYSTEM_animated_image", "SYSTEM_list",
    "SYSTEM_grid", "SYSTEM_table", "SYSTEM_html", "SYSTEM_url",
    "SYSTEM_audio_player", "SYSTEM_video_player", "SYSTEM_media_player",
    "SYSTEM_clock", "SYSTEM_timer", "SYSTEM_weather", "SYSTEM_map",
    "SYSTEM_face",
})

RESERVED_TEMPLATES = frozenset({"SYSTEM_confirm", "SYSTEM_select"})

#: Frame names ovos-bus-client GUIInterface still emits (2.11.x).
LEGACY_TO_SPEC: Dict[str, str] = {
    "SYSTEM_TextFrame": "SYSTEM_text",
    "SYSTEM_ImageFrame": "SYSTEM_image",
    "SYSTEM_AnimatedImageFrame": "SYSTEM_animated_image",
    "SYSTEM_HtmlFrame": "SYSTEM_html",
    "SYSTEM_UrlFrame": "SYSTEM_url",
    "SYSTEM_Status": "SYSTEM_status",
    "SYSTEM_Loading": "SYSTEM_loading",
    "SYSTEM_Face": "SYSTEM_face",
}

#: §5.3: every GUI service MUST deliver these as status events.
STATUS_TOPICS: Tuple[str, ...] = (
    "ovos.listener.wakeword",
    "ovos.listener.record.started",
    "ovos.listener.record.ended",
    "ovos.stt.failed",
    "ovos.utterance.handle",
    "ovos.intent.handler.start",
    "ovos.intent.handler.complete",
    "ovos.intent.handler.error",
    "ovos.intent.unmatched",
    "ovos.utterance.handled",
    "ovos.utterance.speak",
    "ovos.audio.output.visemes",
    "ovos.audio.output.started",
    "ovos.audio.output.ended",
    "ovos.listener.sleep",
    "ovos.listener.awoken",
)

#: §6.9.1: the service keeps the last message per topic and forwards it.
AMBIENT_TOPICS: Tuple[str, ...] = (
    "gui.ambient.weather",
    "gui.ambient.notifications",
)


def is_template_intent(page_name) -> bool:
    """True when ``page_name`` carries the reserved ``SYSTEM_`` prefix (§3.2)."""
    return isinstance(page_name, str) and page_name.startswith(SYSTEM_PREFIX)


def normalize_template(page_name: str, skill_id: str = "") -> str:
    """Map a legacy frame name to its spec name; log every alias used."""
    spec_name = LEGACY_TO_SPEC.get(page_name)
    if spec_name is None:
        return page_name
    LOG.info(f"GUI-1 alias: '{skill_id}' sent legacy page name "
             f"'{page_name}', dispatching as '{spec_name}'")
    return spec_name


def report_unknown_templates(page_names: List[str], skill_id: str) -> None:
    """§3.2 diagnostic for ``SYSTEM_*`` names outside the catalogue."""
    known = SPEC_TEMPLATES | RESERVED_TEMPLATES
    for name in page_names:
        if is_template_intent(name) and name not in known:
            LOG.warning(f"GUI-1 §3.2: '{skill_id}' requested unknown template "
                        f"'{name}'; no conformant adapter will render it")


def is_template_show(page_names: List[str]) -> bool:
    """4.2: a show is a template intent when its FIRST entry is a ``SYSTEM_*`` name."""
    return bool(page_names) and is_template_intent(page_names[0])


def report_mixed_page_names(page_names: List[str], skill_id: str) -> None:
    """One diagnostic for a show that mixes ``SYSTEM_*`` and other page names."""
    kinds = {is_template_intent(name) for name in page_names}
    if len(kinds) > 1:
        path = "template" if is_template_show(page_names) else "legacy page"
        LOG.warning(f"GUI-1 4.2: '{skill_id}' sent mixed page_names {page_names}; "
                    f"the first entry decides, so the active entry takes the {path} path")


def active_template(page_names: List[str], index: Optional[int]) -> str:
    """The entry of ``page_names`` at ``index``, clamped to the list (§4.2)."""
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        index = 0
    return page_names[min(index, len(page_names) - 1)]


def strip_reserved(data: dict) -> dict:
    """Content keys only: every ``__``-prefixed key is protocol metadata (§4.1)."""
    return {k: v for k, v in data.items() if not str(k).startswith("__")}
