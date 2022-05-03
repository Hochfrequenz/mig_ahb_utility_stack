from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestKuendigungMaus:
    """
    A unit test that ensures that the 11016/17/18 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11016.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11016(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11016.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11016_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11017.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11017(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11017.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11017_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11018.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11018(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11018.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11018_maus.json"),
        )
