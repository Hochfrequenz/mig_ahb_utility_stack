from pathlib import Path

import pytest  # type:ignore[import]

from maus.reader.mig_xml_reader import MigXmlReader, check_file_can_be_parsed_as_mig_xml

ALL_MIG_XML_FILES = pytest.mark.datafiles(
    "./migs/FV2204/template_xmls/utilmd_1131.xml",
    "./migs/FV2204/template_xmls/mscons_1154.xml",
    "./migs/FV2204/template_xmls/utilmd_1154.xml",
    "./migs/FV2204/template_xmls/utilmd_2379.xml",
    "./migs/FV2204/template_xmls/utilmd_2380.xml",
    "./migs/FV2204/template_xmls/utilmd_3055.xml",
    "./migs/FV2204/template_xmls/utilmd_7402.xml",
    "./migs/FV2204/template_xmls/utilmd_3225.xml",
    "./migs/FV2204/template_xmls/utilmd_6063.xml",
    "./migs/FV2204/template_xmls/utilmd_9013.xml",
    "./migs/FV2204/template_xmls/utilmd_6411.xml",
    "./migs/FV2204/template_xmls/reqote.xml",
    "./migs/FV2210/template_xmls/utilmd_7143.xml",
    "./migs/FV2210/template_xmls/utilmd_7059.xml",
    "./migs/FV2210/template_xmls/utilmd_7037.xml",
    "./migs/FV2210/template_xmls/utilmd_7037_z02.xml",
)


class TestMigXmlReaderRealData:
    """
    Tests the behaviour of the Message Implementation Guide model with real world example data
    """

    @ALL_MIG_XML_FILES
    def test_is_parsable(self, datafiles):
        check_file_can_be_parsed_as_mig_xml(Path(datafiles) / Path("utilmd_3225.xml"))
        # if no exception is thrown, the test is successful
