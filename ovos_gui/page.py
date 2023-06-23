from socketserver import TCPServer
from ovos_utils.log import LOG


class GuiPage:
    qml_server: TCPServer = None

    def __init__(self, url: str, name: str, persistent: bool, duration: int,
                 server_uri: str = None):
        """
        A GuiPage represents a single GUI Display within a given namespace.
        A Page can either be `persistent` or be removed after some `duration`.
        @param url: URI (local or network path) of the GUI Page
        @param name: Name of the page as shown in its namespace
        @param persistent: If True, page is displayed indefinitely
        @param duration: Number of seconds to display the page for
        @param server_uri: Valid resource URI from the qml_server (if available)
            i.e. skill-ovos-homescreen.openvoiceos/ui/page.qml
        """
        self.url = url
        self.name = name
        self.persistent = persistent
        self.duration = duration
        self.active = False
        if server_uri and not url.startswith('http') and self.qml_server:
            # server_uri isn't a valid URL, only the path portion
            self.url = f"{self.qml_server.url}/{server_uri}"
            LOG.info(f"serving qml file {url} via {self.url}")
