from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestBeginnMsbMaus:
    """
    A unit test that ensures that the 11042/43/44 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11042.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11042(self, datafiles):
        return  # return here to prevent overwriting the 11042 maus file (with manual corrections)
        # remove the return once ttps://github.com/Hochfrequenz/edifact-templates/issues/134 is resolved
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11042.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11042_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11043.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11043(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11043.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11043_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11044.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11044(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11044.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11044_maus.json"),
        )
