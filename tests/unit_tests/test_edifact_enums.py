from typing import Optional

import pytest  # type:ignore[import]
from efoli import EdifactFormat, EdifactFormatVersion

from maus.edifact import EdiMetaData, is_edifact_boilerplate


class TestEdifact:
    """
    Tests the edifact module
    """

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
