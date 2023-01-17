import pytest  # type:ignore[import]

from .helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestEndeMsbMaus:
    """
    A unit test that ensures that the 11051/52/53 MAUS.json are created.
    """
