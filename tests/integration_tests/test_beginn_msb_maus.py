from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestBeginnMsbMaus:
    """
    A unit test that ensures that the 11042/43/44 MAUS.json are created.
    """
