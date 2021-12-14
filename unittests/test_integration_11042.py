from pathlib import Path

import pytest  # type:ignore[import]

from maus import to_deep_ahb
from maus.models.anwendungshandbuch import DeepAnwendungshandbuchSchema
from maus.models.message_implementation_guide import SegmentGroupHierarchySchema
from maus.reader.ahb_csv_reader import AhbCsvReader
from unittests.test_mig import ALL_SGH_FILES  # type:ignore[import]


class TestIntegration11042:
    """
    tests the whole MAUS package on the example of an 11042 AHB
    more of an integration test than a single unit
    """

    @ALL_SGH_FILES
    @pytest.mark.datafiles("./unittests/ahbs/FV2204/UTILMD/11042.csv")
    @pytest.mark.datafiles("./unittests/ahbs/FV2204/UTILMD/11042_deep.json")
    def test_csv_file_reading_11042(self, datafiles):
        path_to_csv: Path = datafiles / "11042.csv"
        reader = AhbCsvReader(file_path=path_to_csv)
        flat_ahb = reader.to_flat_ahb()
        with open(datafiles / "sgh_utilmd.json", "r", encoding="utf-8") as sgh_file:
            sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
        actual = to_deep_ahb(flat_ahb, sgh)
        with open(datafiles / "11042_deep.json", "r", encoding="utf-8") as deep_ahb_file:
            expected_deep_ahb = DeepAnwendungshandbuchSchema().loads(deep_ahb_file.read())
        actual_json = DeepAnwendungshandbuchSchema().dumps(actual, ensure_ascii=True, sort_keys=True)
        assert actual == expected_deep_ahb
