from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestAbmeldeAnfrageMaus:
    """
    A unit test that ensures that the 11010/11/12 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11010.json")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11010_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11010.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11010_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11011.json")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11011_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11011.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11011_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11012.json")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11012_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11012.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11012_maus.json"),
        )
