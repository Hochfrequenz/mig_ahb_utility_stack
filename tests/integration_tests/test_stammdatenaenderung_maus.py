from pathlib import Path

import pytest  # type:ignore[import]

from .helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestStammdatenaenderungMaus:
    """
    A unit test that ensures that the 111xx MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11109.json")
    @pytest.mark.datafiles("../integration_test/edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11109_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11109.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11109_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11115.json")
    @pytest.mark.datafiles("../integration_test/edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11115_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11115.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11115_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11116.json")
    @pytest.mark.datafiles("../integration_test/edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11116_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11116.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11116_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11161.json")
    @pytest.mark.datafiles("../integration_test/edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11161_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11161.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11161_maus.json"),
        )

    # 11170 seems to be gone in FV2210

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11186.json")
    @pytest.mark.datafiles("../integration_test/edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11186_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11186.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11186_maus.json"),
        )
