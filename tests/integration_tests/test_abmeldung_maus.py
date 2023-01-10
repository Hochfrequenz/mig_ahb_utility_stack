from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestAbmeldungMaus:
    """
    A unit test that ensures that the 11007/11008/11009 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11007.json")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11007_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11007.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11007_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11008.json")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11008_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11008.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11008_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11009.json")
    @pytest.mark.datafiles("../unit_tests/migs/FV2210/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11009_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11009.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11009_maus.json"),
        )
