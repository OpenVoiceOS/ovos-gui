from os.path import join, isfile
from typing import Union, Optional
from dataclasses import dataclass
from ovos_utils.log import LOG


@dataclass
class GuiPage:
    """
    A GuiPage represents a single GUI Display within a given namespace.
    A Page can either be `persistent` or be removed after some `duration`.
    Note that a page is generally framework-independent
    @param url: URI (local or network path) of the GUI Page
    @param name: Name of the page as shown in its namespace
    @param persistent: If True, page is displayed indefinitely
    @param duration: Number of seconds to display the page for
    @param namespace: Skill/component identifier
    @param page_id: Page identifier
    """
    url: Optional[str]  # This param is left for backwards-compat.
    name: str
    persistent: bool
    duration: Union[int, bool]
    page_id: Optional[str] = None
    namespace: Optional[str] = None
    resource_dirs: Optional[dict] = None

    active: bool = False

    @property
    def id(self):
        """
        Get a unique identifier for this page.
        """
        return self.page_id or self.url

    def get_uri(self, framework: str = "qt5", server_url: str = None) -> str:
        """
        Get a valid URI for this Page.
        @param framework: String GUI framework to get resources for
        @param server_url: String server URL if available
        @return: Absolute path to the requested resource
        """
        if self.url:
            LOG.warning(f"Static URI: {self.url}")
            return self.url

        if server_url:
            if "://" not in server_url:
                LOG.debug(f"No schema in server_url, assuming 'http'")
                server_url = f"http://{server_url}"
            path = f"{server_url}/{self.namespace}/{framework}/{self.name}"
            LOG.info(f"Resolved server URI: {path}")
            return path
        base_path = self.resource_dirs.get(framework)
        if not base_path and self.resource_dirs.get("all"):
            file_ext = ".qml"
            file_path = join(self.resource_dirs.get('all'), framework,
                             base_path, f"{self.page_id}.{file_ext}")
            if isfile(file_path):
                return file_path
