from pathlib import Path

import pytest  # type:ignore[import]
from helpers import write_to_file_or_assert_equality  # type:ignore[import]

from maus import to_deep_ahb
from maus.deep_ahb_mig_joiner import replace_discriminators_with_edifact_stack
from maus.models.anwendungshandbuch import DeepAnwendungshandbuchSchema
from maus.models.message_implementation_guide import SegmentGroupHierarchySchema
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from maus.reader.mig_reader import MigXmlReader


class TestKuendigungMaus:
    """
    A unit test that ensures that the 11016/17/18 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11016.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11013(self, datafiles):
        path_to_csv: Path = datafiles / "11016.csv"
        reader = FlatAhbCsvReader(file_path=path_to_csv)
        flat_ahb = reader.to_flat_ahb()
        with open(datafiles / "sgh_utilmd.json", "r", encoding="utf-8") as sgh_file:
            sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
        actual_deep_ahb = to_deep_ahb(flat_ahb, sgh)
        actual_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
        mig_reader = MigXmlReader(Path(datafiles) / Path("UTILMD5.2c.template"))
        assert mig_reader is not None
        replace_discriminators_with_edifact_stack(actual_deep_ahb, mig_reader, ignore_errors=False)
        actual_maus_json = DeepAnwendungshandbuchSchema().dumps(
            actual_deep_ahb, ensure_ascii=True, sort_keys=True, indent=True
        )
        assert actual_maus_json is not None
        maus_file_path = Path("edifact-templates/maus/FV2110/UTILMD/11016_maus.json")
        write_to_file_or_assert_equality(actual_deep_ahb, maus_file_path)

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11017.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11014(self, datafiles):
        path_to_csv: Path = datafiles / "11017.csv"
        reader = FlatAhbCsvReader(file_path=path_to_csv)
        flat_ahb = reader.to_flat_ahb()
        with open(datafiles / "sgh_utilmd.json", "r", encoding="utf-8") as sgh_file:
            sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
        actual_deep_ahb = to_deep_ahb(flat_ahb, sgh)
        actual_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
        mig_reader = MigXmlReader(Path(datafiles) / Path("UTILMD5.2c.template"))
        assert mig_reader is not None
        replace_discriminators_with_edifact_stack(actual_deep_ahb, mig_reader, ignore_errors=False)
        actual_maus_json = DeepAnwendungshandbuchSchema().dumps(
            actual_deep_ahb, ensure_ascii=True, sort_keys=True, indent=True
        )
        assert actual_maus_json is not None
        maus_file_path = Path("edifact-templates/maus/FV2110/UTILMD/11017_maus.json")
        write_to_file_or_assert_equality(actual_deep_ahb, maus_file_path)

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11018.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11015(self, datafiles):
        path_to_csv: Path = datafiles / "11018.csv"
        reader = FlatAhbCsvReader(file_path=path_to_csv)
        flat_ahb = reader.to_flat_ahb()
        with open(datafiles / "sgh_utilmd.json", "r", encoding="utf-8") as sgh_file:
            sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
        actual_deep_ahb = to_deep_ahb(flat_ahb, sgh)
        actual_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
        mig_reader = MigXmlReader(Path(datafiles) / Path("UTILMD5.2c.template"))
        assert mig_reader is not None
        replace_discriminators_with_edifact_stack(actual_deep_ahb, mig_reader, ignore_errors=False)
        actual_maus_json = DeepAnwendungshandbuchSchema().dumps(
            actual_deep_ahb, ensure_ascii=True, sort_keys=True, indent=True
        )
        assert actual_maus_json is not None
        maus_file_path = Path("edifact-templates/maus/FV2110/UTILMD/11018_maus.json")
        write_to_file_or_assert_equality(actual_deep_ahb, maus_file_path)
