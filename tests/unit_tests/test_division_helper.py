from typing import Optional

import pytest  # type:ignore[import]

from maus.division_helper import Division, get_division, is_electricity_name, is_gas_name


class TestDivisionHelper:
    """
    Tests the behaviour of the Division Helper.
    """

    @pytest.mark.parametrize(
        "field_name, expected_is_strom",
        [
            pytest.param("Foo", None),
            pytest.param("Gas", False),
            pytest.param("Strom", True),
            pytest.param("Turnusableseintervall des MSB (Strom)", True),
            pytest.param("Geplante Turnusablesung des NB (Gas)", False),
        ],
    )
    def test_is_strom_field(self, field_name: str, expected_is_strom: Optional[bool]):
        actual = is_electricity_name(field_name)
        assert actual == expected_is_strom

    @pytest.mark.parametrize(
        "field_name, expected_is_gas",
        [
            pytest.param("Foo", None),
            pytest.param("Gas", True),
            pytest.param("Strom", False),
            pytest.param("Turnusableseintervall des MSB (Strom)", False),
            pytest.param("Geplante Turnusablesung des NB (Gas)", True),
        ],
    )
    def test_is_gas_field(self, field_name: str, expected_is_gas: Optional[bool]):
        actual = is_gas_name(field_name)
        assert actual == expected_is_gas

    @pytest.mark.parametrize(
        "field_name, expected_division",
        [
            pytest.param(None, None),
            pytest.param("", None),
            pytest.param("Foo", None),
            pytest.param("Gas", Division.GAS),
            pytest.param("Strom", Division.ELECTRICITY),
            pytest.param("Turnusableseintervall des MSB (Strom)", Division.ELECTRICITY),
            pytest.param("Geplante Turnusablesung des NB (Gas)", Division.GAS),
        ],
    )
    def test_get_division(self, field_name: Optional[str], expected_division: Optional[Division]):
        actual = get_division(field_name)
        assert actual == expected_division
