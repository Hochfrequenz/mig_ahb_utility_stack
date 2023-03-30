from pathlib import Path

import pytest  # type:ignore[import]

from .helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestKuendigungMaus:
    """
    A unit test that ensures that the 11016/17/18 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11016.json")
    @pytest.mark.datafiles("/edifact-templates/edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11016_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11016.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11016_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11017.json")
    @pytest.mark.datafiles("/edifact-templates/edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11017_52e(self, datafiles):
        create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11017.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11017_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("../../machine-readable_anwendungshandbuecher/FV2210/UTILMD/flatahb/11018.json")
    @pytest.mark.datafiles("/edifact-templates/edifact-templates/segment_group_hierarchies/FV2210/UTILMD.sgh.json")
    def test_maus_creation_11018_52e(self, datafiles):
        result = create_maus_and_assert(
            flat_ahb_path=Path(datafiles) / "11018.json",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2e.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11018_maus.json"),
        )
        # assert (
        #    len(
        #        result.maus.find_segments(
        #            segment_predicate=lambda seg: seg.section_name == "Datum des bereits bestaetigten Vertragsendes",
        #        )  # the "ae" instead of "ä" is somehow important, we don't want an 'ä' ... for reasons
        #    )
        #    > 0
        # )  # https://github.com/Hochfrequenz/edifact-templates/pull/163 / ED4FTR-24952
