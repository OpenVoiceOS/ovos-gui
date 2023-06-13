import shutil
from hashlib import md5
from os.path import isfile
from ovos_utils.log import LOG


class GuiPage:
    """ A representation of a GUI Page

    A GuiPage represents a single GUI Display within a given namespace. A Page
    has a name, a position and can have either Persistence or Duration during
    which it will exist

    Attributes:
         name: the name of the page that is shown in a given namespace, assigned
         by the skill author
         persistent: indicated weather or not the page itself should persists for a
         period of time or unit the it is removed manually
         duration: the duration of the page in the namespace, assigned by the skill
         author if the page is not persistent
         active: indicates whether the page is currently active in the namespace
    """
    qml_server = None

    def __init__(self, url: str, name: str, persistent: bool, duration: int, contents: str = None):
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
        if not url.startswith("http"):
            if not isfile(url) and contents:
                with open(url, "w") as f:
                    f.write(contents)
            if self.qml_server is not None:
                # TODO: This won't account for the same resources in different
                #   skills/plugins. Need a better way to build a unique parent
                #   directory while preserving structure under `ui`
                fname = url.split('/ui/')[1]
                dst = self.qml_server.qml_path + "/" + fname
                shutil.copy(url.replace("file://", ""), dst)
                self.url = f"http://{self.qml_server.url}/{fname}"
                LOG.info(f"serving qml file {url} from {dst} via {self.url}")
