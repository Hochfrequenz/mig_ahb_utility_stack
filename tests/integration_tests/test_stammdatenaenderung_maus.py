from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestStammdatenaenderungMaus:
    """
    A unit test that ensures that the 111xx MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11109.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11109(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11109.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11109_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11116.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11116(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11116.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11116_maus.json"),
        )

    """
    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11117.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11117(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11117.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11117_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11119.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11119(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11119.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11119_maus.json"),
        )
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11168.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11168(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11168.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11168_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11169.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11169(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11169.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11169_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11170.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11170(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11170.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11170_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11194.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11194(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11194.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11194_maus.json"),
        )
