import os
import shutil
import socketserver
import http.server

from tempfile import gettempdir
from os.path import isdir, join, dirname
from threading import Thread, Event
from ovos_config import Configuration
from ovos_utils.file_utils import get_temp_path


_HTTP_SERVER = None


class QmlFileHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        mimetype = self.guess_type(self.path)
        is_file = not self.path.endswith('/')
        if is_file and any([mimetype.startswith(prefix) for
                           prefix in ("text/", "application/octet-stream")]):
            self.send_header('Content-Type', "text/plain")
            self.send_header('Content-Disposition', 'inline')
        super().end_headers()


def start_qml_http_server(port: int = Configuration().get("gui", {}).get("qml_server_port", 8089)):
    qml_path = get_temp_path("ovos_qml_server")

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
    handler = QmlFileHandler
    http_server = socketserver.TCPServer(("", port), handler)
    _HTTP_SERVER = http_server
    _HTTP_SERVER.qml_path = directory
    started.set()
    http_server.serve_forever()
