"""``gui.page.focus``: a render backend asks for another held entry (GUI-1 amendment B).

The request names a namespace and a zero-based ``page_number`` of its
``page_names``; the session is the one in the Message context. It applies only
to the namespace on top of that session's stack and an entry in range. The
service then makes that entry active and dispatches it through the path the
first entry picks (4.2), so every client of the session stays in step. Any
valid request also restarts the namespace's removal timer, as a touch; one that
names the current entry does only that. Anything else is ignored with one
diagnostic.
"""
from typing import Optional, Tuple

from ovos_bus_client import Message
from ovos_utils.log import LOG

FOCUS_TOPIC = "gui.page.focus"


class PageFocus:
    """Handles ``gui.page.focus`` for a NamespaceManager."""

    def __init__(self, manager, lock):
        self._manager = manager
        self._lock = lock

    def handle(self, message: Message) -> None:
        session_id = self._manager._session_id(message)
        name = message.data.get("namespace")
        page_number = message.data.get("page_number")
        session = self._manager.sessions.get(session_id)
        with self._lock:
            namespace, problem = _target(session, name, page_number)
            if problem:
                LOG.warning(f"GUI-1 {FOCUS_TOPIC} ignored for '{name}' page {page_number!r} "
                            f"in session '{session_id}': {problem}")
                return
            self._manager.restart_removal_timer(namespace, session)
            if page_number == namespace.active_index:
                LOG.debug(f"{FOCUS_TOPIC}: '{name}' already shows entry {page_number}")
                return
            namespace.active_index = page_number
            page_names, data = list(namespace.page_names), dict(namespace.data)
        LOG.info(f"{FOCUS_TOPIC}: '{name}' entry {page_number} is now active in '{session_id}'")
        self._manager.dispatch_entry(name, page_names, page_number, data, session_id)


def _target(session, name, page_number) -> Tuple[Optional[object], Optional[str]]:
    """The namespace a valid request acts on, or the reason the request is ignored."""
    if not isinstance(page_number, int) or isinstance(page_number, bool):
        return None, "page_number is not an integer"
    if session is None or not session.active_namespaces:
        return None, "the session has no active namespace"
    top = session.active_namespaces[0]
    if top.skill_id != name:
        return None, f"the namespace is not on top (top is '{top.skill_id}')"
    if not 0 <= page_number < len(top.page_names):
        return None, f"page_number out of range for {len(top.page_names)} entries"
    return top, None
