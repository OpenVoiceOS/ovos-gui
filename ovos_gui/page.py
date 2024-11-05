from os.path import join, isfile, dirname
from typing import Union, Optional
from dataclasses import dataclass
from ovos_utils.log import LOG
from ovos_gui.constants import GUI_CACHE_PATH


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

    @staticmethod
    def get_file_extension(framework: str) -> str:
        """
        Get a file extension for the specified GUI framework
        @param framework: string framework to get file extension for
        @return: string file extension (empty string if unknown)
        """
        if framework in ("qt5", "qt6"):
            return "qml"
        return ""

    @property
    def res_namespace(self):
        return "system" if self.name.startswith("SYSTEM") else self.namespace

    def get_uri(self, framework: str = "qt5") -> Optional[str]:
        """
        Get a valid URI for this Page.
        @param framework: String GUI framework to get resources for (currently only 'qt5')
        @return: Absolute path to the requested resource
        """
        res_filename = f"{self.name}.{self.get_file_extension(framework)}"
        path = f"{GUI_CACHE_PATH}/{self.res_namespace}/{framework}/{res_filename}"
        LOG.debug(f"Resolved page URI: {path}")
        if isfile(path):
            return path
        LOG.warning(f"Unable to resolve resource file for "
                    f"resource {res_filename} for framework "
                    f"{framework}")
        return None
