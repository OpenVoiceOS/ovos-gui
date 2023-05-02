import os

from ovos_utils.log import LOG


class GuiPage:
    qml_server = None

    def __init__(self, url: str, name: str, persistent: bool, duration: int):
        """
        A GuiPage represents a single GUI Display within a given namespace.
        A Page can either be `persistent` or be removed after some `duration`.
        @param url: URI (local or network path) of the GUI Page
        @param name: Name of the page as shown in its namespace
        @param persistent: If True, page is displayed indefinitely
        @param duration: Number of seconds to display the page for
        """
        self.url = url
        self.name = name
        self.persistent = persistent
        self.duration = duration
        self.active = False
        if self.qml_server is not None and not url.startswith("http"):
            fname = url.split("/")[-1]
            dst = self.qml_server.qml_path + "/" + fname
            os.symlink(url, dst)
            self.url = f"http://{self.qml_server.url}/{fname}"
            LOG.info(f"serving qml file {fname} from {dst} via {self.url}")
