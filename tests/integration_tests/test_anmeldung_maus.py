from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestAnmeldungMaus:
    """
    A unit test that ensures that the 11001/11002/11003 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11001.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11001_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11001.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11001_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11002.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11002_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11002.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11002_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11003.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11003_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11003.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11003_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11004.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11004_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11004.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11004_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11005.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11005_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11005.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11005_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11006.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11006_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11006.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11006_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11023.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11023_52e(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11023.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11023_maus.json"),
        )
