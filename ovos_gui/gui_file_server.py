import http.server
import os
import shutil
import socketserver
from threading import Thread, Event

from ovos_config import Configuration
from ovos_utils.file_utils import get_temp_path
from ovos_utils.log import LOG

_HTTP_SERVER = None


class GuiFileHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        mimetype = self.guess_type(self.path)
        is_file = not self.path.endswith('/')
        if is_file and any([mimetype.startswith(prefix) for
                            prefix in ("text/", "application/octet-stream")]):
            self.send_header('Content-Type', "text/plain")
            self.send_header('Content-Disposition', 'inline')
        super().end_headers()


def start_gui_http_server(qml_path: str, port: int = None):
    """
    Start an http server to host GUI Resources
    @param qml_path: Local file path to server
    @param port: Host port to run file server on
    @return: Initialized HTTP Server
    """
    port = port or Configuration().get("gui", {}).get("file_server_port", 8089)

    if os.path.exists(qml_path):
        shutil.rmtree(qml_path, ignore_errors=True)
    os.makedirs(qml_path, exist_ok=True)

    started_event = Event()
    http_daemon = Thread(target=_initialize_http_server,
                         args=(started_event, qml_path, port),
                         daemon=True)
    http_daemon.start()
    started_event.wait(30)
    return _HTTP_SERVER


def _initialize_http_server(started: Event, directory: str, port: int):
    global _HTTP_SERVER
    os.chdir(directory)
    handler = GuiFileHandler
    http_server = socketserver.TCPServer(("", port), handler)
    _HTTP_SERVER = http_server
    _HTTP_SERVER.qml_path = directory
    _HTTP_SERVER.url = \
        f"{_HTTP_SERVER.server_address[0]}:{_HTTP_SERVER.server_address[1]}"
    LOG.info(f"GUI file server started: {_HTTP_SERVER.url}")
    started.set()
    http_server.serve_forever()
