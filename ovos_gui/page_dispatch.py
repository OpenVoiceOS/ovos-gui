"""Dispatch the active entry with its ``index`` and ``page_count`` (GUI-1 6.3, amendment B).

A template event carries the active entry's zero-based position in the
namespace's ``page_names`` and the length of ``page_names``. A render backend
needs both before it may send ``gui.page.focus``, and the dispatch after a
valid focus is how it learns the new ``index``.

The first ``page_names`` entry picks the hook (4.2): ``dispatch_template`` for a
``SYSTEM_*`` first entry, the legacy ``on_legacy_page`` otherwise. Both values
are passed as keyword arguments, and only to a hook whose signature takes them
(or takes ``**kwargs``), so an adapter written before them is still called.
"""
import inspect
from typing import Callable, Dict, List, Set, Tuple

from ovos_utils.log import LOG

from ovos_gui.gui1 import is_template_show

ENTRY_PARAMS = ("index", "page_count")

_reported_old_hooks: Set[Tuple[type, str]] = set()


def accepts_entry(method: Callable) -> bool:
    """True when ``method`` takes ``index`` and ``page_count`` as keywords."""
    try:
        params = inspect.signature(method).parameters.values()
    except (TypeError, ValueError):
        return False
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params):
        return True
    names = {p.name for p in params}
    return all(name in names for name in ENTRY_PARAMS)


def entry_kwargs(adapter, hook: str, index: int, page_count: int) -> Dict[str, int]:
    """Both values for a hook that takes them, nothing (reported once) for an old one."""
    method = getattr(adapter, hook, None)
    if method is None or accepts_entry(method):
        return {"index": index, "page_count": page_count}
    key = (type(adapter), hook)
    if key not in _reported_old_hooks:
        _reported_old_hooks.add(key)
        LOG.info(f"{type(adapter).__name__}.{hook} takes no index or page_count; "
                 f"calling it without them (GUI-1 6.3)")
    return {}


def accepts_session(method: Callable) -> bool:
    """True when ``method`` takes ``session_id``, a positional argument or ``**kwargs``."""
    try:
        params = list(inspect.signature(method).parameters.values())
    except (TypeError, ValueError):
        return False
    return any(p.name == "session_id" or p.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL)
               or (p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD and p.default is inspect.Parameter.empty)
               for p in params)


def idle_args(adapter, session_id: str) -> Tuple[str, ...]:
    """``(session_id,)`` for an ``on_idle`` that takes it, nothing (reported once) for the old ``on_idle(self)``."""
    method = getattr(adapter, "on_idle", None)
    if method is None or accepts_session(method):
        return (session_id,)
    key = (type(adapter), "on_idle")
    if key not in _reported_old_hooks:
        _reported_old_hooks.add(key)
        LOG.info(f"{type(adapter).__name__}.on_idle takes no session_id; calling it without one (GUI-1 6.3, amendment D)")
    return ()


def dispatch_entry(adapters: List, safe_call: Callable, namespace_name: str,
                   page_names: List[str], index: int, data: dict, session_id: str) -> None:
    """Hand the entry at ``index`` to every adapter through the hook the first entry picks."""
    page = page_names[index]
    if is_template_show(page_names):
        hook, args = "dispatch_template", (page, namespace_name, data, session_id)
    else:
        hook, args = "on_legacy_page", (namespace_name, page, data, session_id)
    for adapter in adapters:
        safe_call(adapter, hook, *args, **entry_kwargs(adapter, hook, index, len(page_names)))
