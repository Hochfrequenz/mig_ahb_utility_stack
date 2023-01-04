from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestEogMaus:
    """
    A unit test that ensures that the 11013/14/16 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11013.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11013_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11013.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11013_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11014.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11014_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11014.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11014_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11015.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11015_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11015.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11015_maus.json"),
        )
