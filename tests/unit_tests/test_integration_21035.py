from pathlib import Path

import pytest  # type:ignore[import]
from test_mig import ALL_SGH_FILES  # type:ignore[import]
from test_mig_xml_reader_real_data import ALL_MIG_XML_FILES  # type:ignore[import]

from maus import to_deep_ahb
from maus.deep_ahb_mig_joiner import replace_discriminators_with_edifact_stack
from maus.models.anwendungshandbuch import DeepAnwendungshandbuchSchema
from maus.models.message_implementation_guide import SegmentGroupHierarchySchema
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from maus.reader.mig_reader import MigXmlReader


class TestIntegration35001:
    """
    tests the whole MAUS package on the example of an 35001 AHB
    more of an integration test than a single unit
    """

    @ALL_SGH_FILES
    @ALL_MIG_XML_FILES
    @pytest.mark.datafiles("./ahbs/FV2204/IFTSTA/21035.csv")
    @pytest.mark.datafiles("./ahbs/FV2204/IFTSTA/21035_deep.json")
    @pytest.mark.datafiles("./ahbs/FV2204/IFTSTA/21035_maus.json")
    def test_csv_file_reading_21035(self, datafiles):
        path_to_csv: Path = datafiles / "21035.csv"
        reader = FlatAhbCsvReader(file_path=path_to_csv)
        flat_ahb = reader.to_flat_ahb()
        with open(datafiles / "sgh_iftsta.json", "r", encoding="utf-8") as sgh_file:
            sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
        actual_deep_ahb = to_deep_ahb(flat_ahb, sgh)
        with open(datafiles / "21035_deep.json", "r", encoding="utf-8") as deep_ahb_file:
            expected_deep_ahb = DeepAnwendungshandbuchSchema().loads(deep_ahb_file.read())
        actual_ahb_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
        assert actual_deep_ahb == expected_deep_ahb
        return
        mig_reader = MigXmlReader(Path(datafiles) / Path("iftsta.xml"))
        assert mig_reader is not None
        replace_discriminators_with_edifact_stack(actual_deep_ahb, mig_reader, ignore_errors=True)
        actual_maus_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
        with open(datafiles / "21035_maus.json", "r", encoding="utf-8") as maus_file:
            expected_maus = DeepAnwendungshandbuchSchema().loads(maus_file.read())
        assert actual_deep_ahb == expected_maus
