from datetime import datetime, timezone
from typing import Optional, Tuple

import pytest  # type:ignore[import]

from maus.edifact import (
    EdifactFormat,
    EdifactFormatVersion,
    EdiMetaData,
    get_current_edifact_format_version,
    get_edifact_format_version,
    get_format_of_pruefidentifikator,
    is_edifact_boilerplate,
)


class TestEdifact:
    """
    Tests the edifact module
    """

    @pytest.mark.parametrize(
        "expectation_tuple",
        [
            ("11042", EdifactFormat.UTILMD),
            ("13002", EdifactFormat.MSCONS),
            ("25001", EdifactFormat.UTILTS),
            ("44001", EdifactFormat.UTILMD),
            ("55001", EdifactFormat.UTILMD),
        ],
    )
    def test_pruefi_to_format(self, expectation_tuple: Tuple[str, EdifactFormat]):
        """
        Tests that the prüfis can be mapped to an EDIFACT format
        """
        assert get_format_of_pruefidentifikator(expectation_tuple[0]) == expectation_tuple[1]

    @pytest.mark.parametrize(
        "key_date,expected_result",
        [
            pytest.param(
                datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                EdifactFormatVersion.FV2104,
                id="Anything before 2021-04-01",
            ),
            pytest.param(datetime(2021, 5, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2104),
            pytest.param(datetime(2021, 10, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2110),
            pytest.param(datetime(2022, 7, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2110),
            pytest.param(datetime(2022, 10, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2210),
            pytest.param(datetime(2022, 10, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2210),
            pytest.param(datetime(2023, 12, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2310),
            pytest.param(datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2310),
            pytest.param(
                datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2310
            ),  # 2404 is valid form 2024-04-03 onwards
            pytest.param(datetime(2024, 4, 2, 22, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2404),
            pytest.param(datetime(2024, 9, 30, 21, 59, 59, tzinfo=timezone.utc), EdifactFormatVersion.FV2404),
            pytest.param(datetime(2024, 9, 30, 22, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2410),
            pytest.param(datetime(2025, 3, 31, 22, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2504),
            pytest.param(datetime(2025, 9, 30, 22, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2510),
            pytest.param(
                datetime(2050, 10, 1, 0, 0, 0, tzinfo=timezone.utc), EdifactFormatVersion.FV2510
            ),  # or what ever is the latest version
        ],
    )
    def test_format_version_from_keydate(self, key_date: datetime, expected_result: EdifactFormatVersion):
        actual = get_edifact_format_version(key_date)
        assert actual == expected_result

    def test_get_current_format_version(self):
        actual = get_current_edifact_format_version()
        assert isinstance(actual, EdifactFormatVersion) is True

    @pytest.mark.parametrize(
        "illegal_pruefi",
        [None, "", "asdas", "01234"],
    )
    def test_illegal_pruefis(self, illegal_pruefi: Optional[str]):
        """
        Test that illegal pruefis are not accepted
        :return:
        """
        with pytest.raises(ValueError):
            get_format_of_pruefidentifikator(illegal_pruefi)  # type:ignore[arg-type] # ok, because this raises an error

    def test_edi_meta_data_instantiation(self):
        actual = EdiMetaData(
            pruefidentifikator="11042",
            edifact_format=EdifactFormat.UTILMD,
            edifact_format_version=EdifactFormatVersion.FV2210,
        )
        assert isinstance(actual, EdiMetaData) is True

    def test_edi_meta_data_instantiation_with_default_format(self):
        actual = EdiMetaData(
            pruefidentifikator="11042",
            edifact_format_version=EdifactFormatVersion.FV2210,
        )
        assert isinstance(actual, EdiMetaData) is True
        assert actual.edifact_format == EdifactFormat.UTILMD

    def test_edi_meta_data_instantiation_with_error(self):
        with pytest.raises(ValueError) as value_error:
            _ = EdiMetaData(
                pruefidentifikator="13002",  # <-- 13002 is not a UTILMD pruefi
                edifact_format=EdifactFormat.UTILMD,
                edifact_format_version=EdifactFormatVersion.FV2210,
            )
        assert (
            f"{13002}' is incompatible with '{EdifactFormat.UTILMD}'; expected '{EdifactFormat.MSCONS}' instead"
            in str(value_error)
        )

    @pytest.mark.parametrize("pruefi", [pytest.param("10000")])
    def test_pruefi_to_format_not_mapped_exception(self, pruefi: str):
        """
        Test that pruefis that are not mapped to an edifact format are not accepted
        """
        with pytest.raises(ValueError) as excinfo:
            _ = get_format_of_pruefidentifikator(pruefi)

        assert "No Edifact format was found for pruefidentifikator" in excinfo.value.args[0]

    @pytest.mark.parametrize(
        "segment_code,expected_is_boilerplate",
        [
            pytest.param(None, True),
            pytest.param("UNH", False),
            pytest.param("UNT", True),
            pytest.param("UNZ", True),
            pytest.param("DTM", False),
        ],
    )
    def test_is_boilerplate_segment(self, segment_code: Optional[str], expected_is_boilerplate: bool):
        actual_is_boilerplate = is_edifact_boilerplate(segment_code)
        assert actual_is_boilerplate == expected_is_boilerplate
