from typing import Union, Optional
from dataclasses import dataclass
from ovos_utils.log import LOG


@dataclass
class GuiPage:
    """
    A GuiPage represents a single GUI Display within a given namespace.
    A Page can either be `persistent` or be removed after some `duration`.
    Note that a page is generally framework-independent
    @param name: Name of the page as shown in its namespace (could
    @param persistent: If True, page is displayed indefinitely
    @param duration: Number of seconds to display the page for
    @param namespace: Skill/component identifier
    """
    name: str
    persistent: bool
    duration: Union[int, bool]
    namespace: Optional[str] = None
