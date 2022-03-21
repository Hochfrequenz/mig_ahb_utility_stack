from typing import Optional

import pytest  # type:ignore[import]

from maus.reader.mig_ahb_name_helpers import are_similar_names


class TestMigAhbNameHelpers:
    """
    Tests the behaviour of static helper methods
    """

    @pytest.mark.parametrize(
        "x,y, expected_result",
        [
            pytest.param(None, "", True),
            pytest.param("", "", True),
            pytest.param("X", "X", True),
            pytest.param("X", "x", True),
            pytest.param("X", "y", False),
            pytest.param("Gültigkeit, Beginndatum", "Gültigkeit,Beginndatum", True),
            pytest.param(
                "Referenz Vorgangsnummer (aus Anfragenachricht)", "Referenz Vorgangsnummer (aus Anfragenachricht)", True
            ),
        ],
    )
    def test_are_similar_names(self, x: Optional[str], y: Optional[str], expected_result: bool):
        actual = are_similar_names(x, y)
        assert actual == expected_result
