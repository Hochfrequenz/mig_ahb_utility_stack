import pytest  # type:ignore[import]

from .helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestKuendigungMsbMaus:
    """
    A unit test that ensures that the 11039/40/41 MAUS.json are created.
    """
