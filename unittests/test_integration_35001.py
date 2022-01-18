from pathlib import Path

import pytest  # type:ignore[import]
from test_mig_xml_reader import ALL_MIG_XML_FILES

from maus import to_deep_ahb
from maus.deep_ahb_mig_joiner import replace_discriminators_with_edifact_stack
from maus.models.anwendungshandbuch import DeepAnwendungshandbuchSchema
from maus.models.message_implementation_guide import SegmentGroupHierarchySchema
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from maus.reader.mig_reader import MigXmlReader
from unittests.test_mig import ALL_SGH_FILES  # type:ignore[import]


class TestIntegration35001:
    """
    tests the whole MAUS package on the example of an 35001 AHB
    more of an integration test than a single unit
    """

    @ALL_SGH_FILES
    @ALL_MIG_XML_FILES
    @pytest.mark.datafiles("./unittests/ahbs/FV2204/REQOTE/35001.csv")
    @pytest.mark.datafiles("./unittests/ahbs/FV2204/REQOTE/35001_deep.json")
    @pytest.mark.datafiles("./unittests/ahbs/FV2204/REQOTE/35001_maus.json")
    def test_csv_file_reading_35001(self, datafiles):
        path_to_csv: Path = datafiles / "35001.csv"
        reader = FlatAhbCsvReader(file_path=path_to_csv)
        flat_ahb = reader.to_flat_ahb()
        with open(datafiles / "sgh_reqote.json", "r", encoding="utf-8") as sgh_file:
            sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
        actual_deep_ahb = to_deep_ahb(flat_ahb, sgh)
        with open(datafiles / "35001_deep.json", "r", encoding="utf-8") as deep_ahb_file:
            expected_deep_ahb = DeepAnwendungshandbuchSchema().loads(deep_ahb_file.read())
        actual_ahb_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
        assert actual_deep_ahb == expected_deep_ahb
        mig_reader = MigXmlReader(Path(datafiles) / Path("reqote.xml"))
        assert mig_reader is not None
        replace_discriminators_with_edifact_stack(actual_deep_ahb, mig_reader)
        actual_maus_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
        with open(datafiles / "35001_maus.json", "r", encoding="utf-8") as maus_file:
            expected_maus = DeepAnwendungshandbuchSchema().loads(maus_file.read())
        assert actual_deep_ahb == expected_maus
