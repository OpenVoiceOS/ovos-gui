"""The system GUI resource cache is built by several processes at once.

`NamespaceManager._cache_system_resources` runs from
`NamespaceManager.__init__`, and the path it builds,
`$XDG_CACHE_HOME/ovos_gui/system`, carries no process identity at all. Every
process that starts a NamespaceManager under one `XDG_CACHE_HOME` therefore
builds one directory: a restart that overlaps the previous run, or a second
container sharing the cache root.

The reader is `ovos_gui/page.py`, which resolves
`{GUI_CACHE_PATH}/{namespace}/{framework}/{file}` by name, so a tree that is
missing or half filled is served that way.

Every worker below calls the production method. A `NamespaceManager` built
with `__new__` and given `_system_res_dir` reaches `_cache_system_resources`
without a bus, so the code under test is the code that ships, and the suite
runs on a tree that does not carry the fix — which is what makes a red run
there mean the defect rather than a missing attribute.

`XDG_CACHE_HOME` is set in each worker before `ovos_gui` is imported, so
`GUI_CACHE_PATH` resolves under the test's own directory. The workers are
spawned, so each gets a fresh import.

A race does not fail every time. One green run proves nothing here; the count
over many builds is the evidence, and the control is this same probe against
a tree without the fix.
"""
import multiprocessing
import os
import shutil
import tempfile
import time
import unittest

# three builders against one cache root, and a reader watching the served
# tree while they work
WORKERS = 3
BUILDS_PER_WORKER = 25
READ_SECONDS = 6.0

# what the shipped system resource directory looks like: a framework
# directory holding files the reader resolves by name
FRAMEWORK = "qt5"
FILE_NAMES = [f"page_{i}.qml" for i in range(12)]


def _make_source(root: str) -> str:
    """Build a stand-in for ovos_gui/res/gui."""
    src = os.path.join(root, "res_gui")
    os.makedirs(os.path.join(src, FRAMEWORK), exist_ok=True)
    for name in FILE_NAMES:
        with open(os.path.join(src, FRAMEWORK, name), "w") as handle:
            handle.write(f"// {name}\n")
    return src


def _manager(src: str):
    """A NamespaceManager that can cache resources and nothing else.

    `__init__` needs a bus and starts the whole GUI service. The method under
    test reads one attribute, so the object is built without running
    `__init__` and given that attribute.
    """
    from ovos_gui.namespace import NamespaceManager
    mgr = NamespaceManager.__new__(NamespaceManager)
    mgr._system_res_dir = src
    return mgr


def _build_worker(cache_home: str, src: str, builds: int, errors):
    """Call the production method repeatedly, as restarting services would."""
    os.environ["XDG_CACHE_HOME"] = cache_home  # before ovos_gui is imported
    mgr = _manager(src)
    for _ in range(builds):
        try:
            mgr._cache_system_resources()
        except Exception as e:  # noqa: BLE001 - the probe reports, not raises
            errors.append(f"build: {type(e).__name__}: {e}")


def _read_worker(cache_home: str, seconds: float, errors, saw):
    """Read the served tree the way ovos_gui.page resolves a resource.

    Bounded by wall clock rather than by a read count: a reader that finishes
    before the first build has published anything sees nothing and reports no
    partial tree, which is the answer the change wants and is worthless.
    `saw` counts the reads that found a tree, so a run where the reader never
    overlapped a build fails loudly instead of passing quietly.
    """
    os.environ["XDG_CACHE_HOME"] = cache_home
    from ovos_gui.constants import GUI_CACHE_PATH
    served = f"{GUI_CACHE_PATH}/system/{FRAMEWORK}"
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            present = set(os.listdir(served))
        except FileNotFoundError:
            continue  # nothing published yet, or the tree is between builds
        except OSError as e:
            errors.append(f"read: {type(e).__name__}: {e}")
            continue
        saw.value += 1
        missing = set(FILE_NAMES) - present
        if missing:
            errors.append(f"read: served tree is incomplete, missing "
                          f"{len(missing)} of {len(FILE_NAMES)}")


class TestTheSystemCacheIsNeverServedHalfBuilt(unittest.TestCase):
    """A reader must never see the served tree missing or partly filled."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="ovos-gui-system-cache-")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.cache_home = os.path.join(self._tmp, "xdg-cache")
        self.cache_path = os.path.join(self.cache_home, "ovos_gui")
        self.src = _make_source(self._tmp)

    def _build(self, builds: int):
        """Run one builder in a spawned process and return its errors."""
        ctx = multiprocessing.get_context("spawn")
        with multiprocessing.Manager() as manager:
            errors = manager.list()
            p = ctx.Process(target=_build_worker,
                            args=(self.cache_home, self.src, builds, errors))
            p.start()
            p.join(timeout=180)
            self.assertFalse(p.is_alive(), "the builder did not finish")
            return list(errors)

    def test_concurrent_builds_never_expose_an_incomplete_tree(self):
        ctx = multiprocessing.get_context("spawn")
        with multiprocessing.Manager() as manager:
            errors = manager.list()
            saw = manager.Value("i", 0)
            procs = [ctx.Process(target=_build_worker,
                                 args=(self.cache_home, self.src,
                                       BUILDS_PER_WORKER, errors))
                     for _ in range(WORKERS)]
            procs.append(ctx.Process(
                target=_read_worker,
                args=(self.cache_home, READ_SECONDS, errors, saw)))
            for p in procs:
                p.start()
            for p in procs:
                p.join(timeout=180)
                self.assertFalse(p.is_alive(), "a worker did not finish")
            found = list(errors)
            reads_that_saw_a_tree = saw.value

        self.assertGreater(
            reads_that_saw_a_tree, 0,
            "the reader never saw the served tree, so it measured nothing; "
            "such a run reports no partial read whatever the code does")
        self.assertEqual(
            found, [],
            f"{len(found)} failure(s) over "
            f"{WORKERS * BUILDS_PER_WORKER} builds and "
            f"{reads_that_saw_a_tree} reads that saw a tree; "
            f"first few: {found[:5]}")

    def test_the_tree_left_behind_is_complete(self):
        """After a build, the served tree holds every file."""
        self.assertEqual(self._build(3), [])
        served = f"{self.cache_path}/system/{FRAMEWORK}"
        self.assertTrue(os.path.isdir(served))
        self.assertEqual(sorted(os.listdir(served)), sorted(FILE_NAMES))

    def test_no_staging_directory_is_left_behind(self):
        """A staging directory that outlived its build would be served as a
        namespace by anything that lists the cache root."""
        self.assertEqual(self._build(3), [])
        leftovers = [n for n in os.listdir(self.cache_path)
                     if n.startswith(".system.staging.")]
        self.assertEqual(leftovers, [])

    def test_a_stale_file_where_the_directory_belongs_is_replaced(self):
        """Something left a plain file at the served path. A directory cannot
        be renamed onto one, so it has to be removed first."""
        os.makedirs(self.cache_path, exist_ok=True)
        with open(f"{self.cache_path}/system", "w") as handle:
            handle.write("not a directory")
        self.assertEqual(self._build(1), [])
        self.assertTrue(
            os.path.isdir(f"{self.cache_path}/system/{FRAMEWORK}"))

    def test_the_served_tree_keeps_the_source_mode(self):
        """`mkdtemp` creates the staging directory at 0700 and `os.rename`
        carries the mode with the inode, so the served tree has to take its
        mode from the source instead. reviewer-b measured this exact trap on
        the sibling change in ovos-bus-client#380."""
        self.assertEqual(self._build(1), [])
        served = f"{self.cache_path}/system"
        self.assertEqual(oct(os.stat(served).st_mode & 0o777),
                         oct(os.stat(self.src).st_mode & 0o777))


if __name__ == "__main__":
    unittest.main()
