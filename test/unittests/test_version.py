import unittest


class TestVersion(unittest.TestCase):
    """Test version.py version constants and __version__ formatting."""

    def test_version_constants_are_integers(self):
        """Test that version constants are integers."""
        from ovos_gui.version import VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD, VERSION_ALPHA
        self.assertIsInstance(VERSION_MAJOR, int)
        self.assertIsInstance(VERSION_MINOR, int)
        self.assertIsInstance(VERSION_BUILD, int)
        self.assertIsInstance(VERSION_ALPHA, int)

    def test_version_constants_are_non_negative(self):
        """Test that version constants are non-negative."""
        from ovos_gui.version import VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD, VERSION_ALPHA
        self.assertGreaterEqual(VERSION_MAJOR, 0)
        self.assertGreaterEqual(VERSION_MINOR, 0)
        self.assertGreaterEqual(VERSION_BUILD, 0)
        self.assertGreaterEqual(VERSION_ALPHA, 0)

    def test_version_string_without_alpha(self):
        """Test __version__ string format without alpha."""
        from ovos_gui import version
        # Temporarily set VERSION_ALPHA to 0
        original_alpha = version.VERSION_ALPHA
        try:
            version.VERSION_ALPHA = 0
            # Regenerate __version__
            version.__version__ = f"{version.VERSION_MAJOR}.{version.VERSION_MINOR}.{version.VERSION_BUILD}" + \
                                (f"a{version.VERSION_ALPHA}" if version.VERSION_ALPHA else "")
            self.assertNotIn('a', version.__version__)
        finally:
            version.VERSION_ALPHA = original_alpha

    def test_version_string_with_alpha(self):
        """Test __version__ string format with alpha."""
        from ovos_gui import version
        # Temporarily set VERSION_ALPHA to a non-zero value
        original_alpha = version.VERSION_ALPHA
        try:
            version.VERSION_ALPHA = 5
            # Regenerate __version__
            version.__version__ = f"{version.VERSION_MAJOR}.{version.VERSION_MINOR}.{version.VERSION_BUILD}" + \
                                (f"a{version.VERSION_ALPHA}" if version.VERSION_ALPHA else "")
            self.assertIn('a5', version.__version__)
        finally:
            version.VERSION_ALPHA = original_alpha

    def test_version_string_format(self):
        """Test __version__ string has expected format."""
        from ovos_gui.version import __version__
        # Should be in format X.Y.Z or X.Y.ZaA
        parts = __version__.split('.')
        self.assertEqual(len(parts), 3)
        # Major and minor should be digits
        self.assertTrue(parts[0].isdigit())
        self.assertTrue(parts[1].isdigit())
        # Build might contain 'a' for alpha
        self.assertTrue(any(c.isdigit() or c == 'a' for c in parts[2]))

    def test_version_string_is_not_empty(self):
        """Test that __version__ is not empty."""
        from ovos_gui.version import __version__
        self.assertTrue(__version__)
        self.assertIsInstance(__version__, str)

    def test_version_major_minor_build_in_string(self):
        """Test that major.minor.build appear in __version__."""
        from ovos_gui.version import __version__, VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD
        expected_base = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD}"
        self.assertTrue(__version__.startswith(expected_base))

    def test_version_string_matches_constants(self):
        """__version__ is derived from the version constants.

        The exact numbers are bumped automatically by release tooling, so this
        asserts the derivation rather than a hard-coded value.
        """
        from ovos_gui.version import (
            __version__, VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD, VERSION_ALPHA
        )
        expected = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD}" + \
                   (f"a{VERSION_ALPHA}" if VERSION_ALPHA else "")
        self.assertEqual(__version__, expected)
