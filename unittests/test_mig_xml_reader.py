from pathlib import Path
from typing import Optional

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]

from maus.reader.mig_reader import MigXmlReader

ALL_MIG_XML_FILES = pytest.mark.datafiles(
    "./unittests/migs/FV2204/template_xmls/mscons_1154.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_1154.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_2380.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_7402.xml",
)


class TestMigXmlReader:
    """
    Tests the behaviour of the Message Implementation Guide model
    """

    @pytest.mark.parametrize(
        "xml_string, expected_format",
        [
            pytest.param('<?xml version="1.0"?><MSCONS></MSCONS>', "MSCONS"),
            pytest.param('<?xml version="1.0"?><UTILMD></UTILMD>', "UTILMD"),
        ],
    )
    def test_get_edifact_format(self, xml_string: str, expected_format: str):
        reader = MigXmlReader(xml_string)
        assert reader.get_format_name() == expected_format

    @pytest.mark.parametrize(
        "x,y, expected_result",
        [
            pytest.param(None, "", True),
            pytest.param("", "", True),
            pytest.param("X", "X", True),
            pytest.param("X", "x", True),
            pytest.param("X", "y", False),
            pytest.param("Gültigkeit, Beginndatum", "Gültigkeit,Beginndatum", True),
            pytest.param(
                "Referenz Vorgangsnummer (aus Anfragenachricht)", "Referenz Vorgangsnummer (aus Anfragenachricht)", True
            ),
        ],
    )
    def test_are_similar_names(self, x: Optional[str], y: Optional[str], expected_result: bool):
        actual = MigXmlReader.are_similar_names(x, y)
        assert actual == expected_result

    def test_make_tree_names_comparable(self):
        orig_xml = """<?xml version="1.0"?>
        <hello>
        <einfield name="Foo "/>
        <einclass ahbName="Hallo-Welt">
            <einfield name=" DiGiTaLiSiErUnG" ahbName="(ZuKunFt)"/>
        </einclass>
        </hello>
        """
        tree = etree.ElementTree(etree.fromstring(orig_xml))
        MigXmlReader.make_tree_names_comparable(tree)
        for element in tree.iter():
            if "name" in element.attrib:
                assert element.attrib["name"] == MigXmlReader.make_name_comparable(element.attrib["name"])
            if "ahbName" in element.attrib:
                assert element.attrib["ahbName"] == MigXmlReader.make_name_comparable(element.attrib["ahbName"])

    @ALL_MIG_XML_FILES
    @pytest.mark.parametrize(
        "mig_xml_path, segment_group_key, segment_key, data_element_id, name, previous_qualifier, expected_path",
        [
            pytest.param(
                "mscons_1154.xml",
                "SG1",
                "RFF",
                "1154",
                "Prüfidentifikator",
                None,
                '$["Dokument"][0]["Nachricht"][0]["Prüfidentifikator"][0]["ID"]',
                id="mscons pruefi",
            ),
            pytest.param(
                "utilmd_7402.xml",
                "SG4",
                "IDE",
                "7402",
                "Vorgangsnummer",
                None,
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Vorgangsnummer"]',
                id="utilmd vorgangsnummer",
            ),
            pytest.param(
                "utilmd_2380.xml",
                "root",
                "DTM",
                "2380",
                "Gültigkeit, Beginndatum",
                None,
                '$["Dokument"][0]["Nachricht"][0]["Gültigkeit,Beginndatum"]',
                id="gueltigkeit,beginndatum",
            ),
            pytest.param(
                "utilmd_2380.xml",
                "SG4",
                "DTM",
                "2380",
                "Bilanzierungsbeginn",
                None,
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Bilanzierungsbeginn"]',
                id="utilmd bilanzierungsbeginn",
            ),
            pytest.param(
                "utilmd_1154.xml",
                "SG6",
                "RFF",
                "1154",
                "Referenz Vorgangsnummer(aus Anfragenachricht)",
                None,
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Referenz Vorgangsnummer (aus Anfragenachricht)"][0]["Referenz"]',
                id="referenz aus anfragenachricht",
            ),
            pytest.param(
                "utilmd_1154.xml",
                "SG8",
                "RFF",
                "1154",
                "Referenz auf die ID einer Messlokation",
                "Z19",
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Erforderliche OBIS-Daten der Messlokation"][0]["Referenz auf die ID einer Messlokation"]',
                id="referenz auf melo-id",
            ),
        ],
    )
    def test_simple_paths(
        self,
        datafiles,
        mig_xml_path: str,
        segment_group_key: str,
        segment_key: str,
        data_element_id: str,
        name: str,
        previous_qualifier: Optional[str],
        expected_path: str,
    ):
        reader = MigXmlReader(Path(datafiles) / mig_xml_path)
        actual_stack = reader.get_edifact_stack(
            segment_group_key, segment_key, data_element_id, name  # , previous_qualifier
        )
        assert actual_stack.to_json_path() == expected_path
