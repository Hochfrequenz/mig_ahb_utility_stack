from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestAbmeldeAnfrageMaus:
    """
    A unit test that ensures that the 11010/11/12 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11010.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11010_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11010.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11010_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11011.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11011_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11011.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11011_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11012.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11012_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11012.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11012_maus.json"),
        )
