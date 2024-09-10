from os.path import join, isfile, dirname
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
    @param name: Name of the page as shown in its namespace (could
    @param persistent: If True, page is displayed indefinitely
    @param duration: Number of seconds to display the page for
    @param namespace: Skill/component identifier
    @param page_id: Page identifier
        (file path relative to gui_framework directory with no extension)
    """
    url: Optional[str]  # This param is left for backwards-compat.
    name: str
    persistent: bool
    duration: Union[int, bool]
    page_id: Optional[str] = None
    namespace: Optional[str] = None
    resource_dirs: Optional[dict] = None

    @property
    def id(self):
        """
        Get a unique identifier for this page.
        """
        return self.page_id or self.url

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

    def get_uri(self, framework: str = "qt5", server_url: str = None) -> str:
        """
        Get a valid URI for this Page.
        @param framework: String GUI framework to get resources for
        @param server_url: String server URL if available; this could be for a
            web server (http://), or a container host path (file://)
        @return: Absolute path to the requested resource
        """
        if self.url:
            LOG.warning(f"Static URI: {self.url}")
            return self.url

        res_filename = f"{self.page_id}.{self.get_file_extension(framework)}"
        res_namespace = "system" if self.page_id.startswith("SYSTEM") else \
            self.namespace
        if server_url:
            if "://" not in server_url:
                if server_url.startswith("/"):
                    LOG.debug(f"No schema in server_url, assuming 'file'")
                    server_url = f"file://{server_url}"
                else:
                    LOG.debug(f"No schema in server_url, assuming 'http'")
                    server_url = f"http://{server_url}"
            path = f"{server_url}/{res_namespace}/{framework}/{res_filename}"
            LOG.info(f"Resolved server URI: {path}")
            return path
        base_path = self.resource_dirs.get(framework)
        if not base_path and self.resource_dirs.get("all"):
            file_path = join(self.resource_dirs.get('all'), framework,
                             res_filename)
        else:
            file_path = join(base_path, res_filename)
        if isfile(file_path):
            return file_path
        # Check system resources
        file_path = join(dirname(__file__), "res", "gui", framework,
                         res_filename)
        if isfile(file_path):
            return file_path
        raise FileNotFoundError(f"Unable to resolve resource file for "
                                f"resource {res_filename} for framework "
                                f"{framework}")
