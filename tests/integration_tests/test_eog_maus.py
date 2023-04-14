from pathlib import Path

import pytest  # type:ignore[import]

from .helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestEogMaus:
    """
    A unit test that ensures that the 11013/14/16 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11013.json")
    @pytest.mark.datafiles("./edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11013_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11013.json",
            sgh_path=Path(datafiles) / "UTILMD.sgh.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11013_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11014.json")
    @pytest.mark.datafiles("./edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11014_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11014.json",
            sgh_path=Path(datafiles) / "UTILMD.sgh.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11014_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11015.json")
    @pytest.mark.datafiles("./edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11015_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11015.json",
            sgh_path=Path(datafiles) / "UTILMD.sgh.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11015_maus.json"),
        )
