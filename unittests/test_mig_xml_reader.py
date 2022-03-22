from pathlib import Path
from typing import Optional, Tuple

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]
from lxml.etree import Element

from maus.models.edifact_components import EdifactStackQuery
from maus.reader.mig_reader import MigXmlReader

ALL_MIG_XML_FILES = pytest.mark.datafiles(
    "./unittests/migs/FV2204/template_xmls/mscons_1154.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_1154.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_2379.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_2380.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_7402.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_3225.xml",
    "./unittests/migs/FV2204/template_xmls/utilmd_9013.xml",
    "./unittests/migs/FV2204/template_xmls/reqote.xml",
    # "./unittests/migs/FV2204/template_xmls/utilmd.xml",
    # "./unittests/migs/FV2204/template_xmls/iftsta.xml",
)


class TestMigXmlReader:
    """
    Tests the behaviour of the Message Implementation Guide model
    """

    @staticmethod
    def _prepare_xml_reader_and_element(xml_string: str, element_xpath: str) -> Tuple[MigXmlReader, Element]:
        """
        A helper method for easier test setup
        """
        reader = MigXmlReader(xml_string)
        elements = reader._original_tree.xpath(element_xpath)
        if len(elements) != 1:
            raise ValueError(
                f"In this test you're thought to provide an xpath that matches exactly one element of the given XML but found {len(elements)}."
            )
        element = elements[0]
        return reader, element

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
        "xml_string, element_xpath, use_sanitized, expected_result",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42"><foo/></class></MSCONS>',
                "//MSCONS/class/foo",
                False,
                "SG42",
            ),
        ],
    )
    def test_get_parent_segment_group(
        self, xml_string: str, element_xpath: str, use_sanitized: bool, expected_result: Optional[str]
    ):
        reader, element = TestMigXmlReader._prepare_xml_reader_and_element(xml_string, element_xpath)
        actual = reader.get_parent_segment_group_key(element, use_sanitized_tree=use_sanitized)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string, element_xpath, use_sanitized, expected_result",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><foo key="DTM:1:2[1:0=Z21]"><bar/></foo></MSCONS>',
                "//MSCONS/foo/bar",
                False,
                "Z21",
            ),
        ],
    )
    def test_get_parent_predecessor(
        self, xml_string: str, element_xpath: str, use_sanitized: bool, expected_result: Optional[str]
    ):
        reader, element = TestMigXmlReader._prepare_xml_reader_and_element(xml_string, element_xpath)
        actual = reader.get_parent_predecessor(element, use_sanitized_tree=use_sanitized)
        assert actual == expected_result

    @ALL_MIG_XML_FILES
    @pytest.mark.parametrize(
        "mig_xml_path, query, expected_path",
        [
            pytest.param(
                "mscons_1154.xml",
                EdifactStackQuery(
                    segment_group_key="SG1", segment_code="RFF", data_element_id="1154", name="Prüfidentifikator"
                ),
                '$["Dokument"][0]["Nachricht"][0]["Prüfidentifikator"][0]["ID"]',
                id="mscons pruefi",
            ),
            pytest.param(
                "utilmd_7402.xml",
                EdifactStackQuery(
                    segment_group_key="SG4", segment_code="IDE", data_element_id="7402", name="Vorgangsnummer"
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Vorgangsnummer"]',
                id="utilmd vorgangsnummer",
            ),
            pytest.param(
                "utilmd_2380.xml",
                EdifactStackQuery(
                    segment_group_key="root", segment_code="DTM", data_element_id="2380", name="Gültigkeit, Beginndatum"
                ),
                '$["Dokument"][0]["Nachricht"][0]["Gültigkeit,Beginndatum"]',
                id="gueltigkeit,beginndatum",
            ),
            pytest.param(
                "utilmd_2380.xml",
                EdifactStackQuery(
                    segment_group_key="SG4", segment_code="DTM", data_element_id="2380", name="Bilanzierungsbeginn"
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Bilanzierungsbeginn"]',
                id="utilmd bilanzierungsbeginn",
            ),
            pytest.param(
                "utilmd_1154.xml",
                EdifactStackQuery(
                    segment_group_key="SG6",
                    segment_code="RFF",
                    data_element_id="1154",
                    name="Referenz Vorgangsnummer(aus Anfragenachricht)",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Referenz Vorgangsnummer (aus Anfragenachricht)"][0]["Referenz"]',
                id="referenz aus anfragenachricht",
            ),
            pytest.param(
                "utilmd_1154.xml",
                EdifactStackQuery(
                    segment_group_key="SG8",
                    segment_code="RFF",
                    data_element_id="1154",
                    name="Referenz auf die ID einer Messlokation",
                    predecessor_qualifier="Z19",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Erforderliche OBIS-Daten der Messlokation"][0]["Referenz auf die ID einer Messlokation"]',
                id="referenz auf melo-id",
            ),
            pytest.param(
                "reqote.xml",
                EdifactStackQuery(
                    segment_group_key="root",
                    segment_code="DTM",
                    data_element_id="2380",
                    name="Datum oder Uhrzeit oderZeitspanne, Wert",
                    # <-- the messed up spaces are due to line breaks in the PDF
                    predecessor_qualifier="76",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Datum zum geplanten Leistungsbeginn"]',
                id="reqote lieferdatum",
            ),
            pytest.param(
                "reqote.xml",
                EdifactStackQuery(
                    segment_group_key="SG11",
                    segment_code="NAD",
                    data_element_id="3039",
                    name="MP-ID",  # <-- this used to be "Beteiligter, Identifikation"... don't know why
                    predecessor_qualifier="MS",
                ),
                '$["Dokument"][0]["Nachricht"][0]["MP-ID Absender"][0]["MP-ID"]',
                id="reqote absender",
            ),
            pytest.param(
                "reqote.xml",
                EdifactStackQuery(
                    segment_group_key="SG11",
                    segment_code="NAD",
                    data_element_id="3055",
                    name=None,
                    predecessor_qualifier="MS",
                ),
                '$["Dokument"][0]["Nachricht"][0]["MP-ID Absender"][0]["Codeliste"]',
                id="reqote absender codeliste",
            ),
            pytest.param(
                "utilmd_9013.xml",
                EdifactStackQuery(
                    segment_group_key="SG4",
                    segment_code="STS",
                    data_element_id="9013",
                    name=None,
                    predecessor_qualifier="7",
                ),
                '$["Dokument"][0]["Vorgang"][0]["Transaktionsgrund"]',
                id="UTILMD Transaktionsgrund",
            ),
            pytest.param(
                "utilmd_3225.xml",
                EdifactStackQuery(
                    segment_group_key="SG5",
                    segment_code="LOC",
                    data_element_id="3225",
                    name="Identifikator",  # <-- name in AHB != name in MIG ("ID")
                    predecessor_qualifier="172",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Meldepunkt"][0]["ID"]',
                id="UTILMD: LOC ID vs. Identifikator",
            ),
            pytest.param(
                "utilmd_1154.xml",
                EdifactStackQuery(
                    segment_group_key="SG6",
                    segment_code="RFF",  # this is a reference
                    data_element_id="1154",
                    name="ID der Marktlokation",  # <-- name in AHB != name in MIG ("ID")
                    predecessor_qualifier="Z18",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Referenz auf die ID der Marktlokation für Termine der Marktlokation"][0]["ID"]',
                id="UTILMD: LOC ID der MaLo Z18",
            ),
            pytest.param(
                "utilmd_2380.xml",
                EdifactStackQuery(
                    segment_group_key="SG6",
                    segment_code="DTM",
                    data_element_id="2380",
                    name="Datum oder Uhrzeit oderZeitspanne, Wert",
                    predecessor_qualifier="752",
                    section_name="Geplante Turnusablesung des MSB (Strom)"
                    # division=Division.ELECTRICITY,
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Geplante Turnusablesung des MSB (Strom)"]',
                id="UTILMD geplante Turnusablesung 752",
            ),
            # pytest.param( # unsolved
            #    "utilmd_1154.xml",
            # EdifactStackQuery(segment_group_key='SG8', segment_code='RFF', data_element_id='1154',
            #                  name='ID der Marktlokation', predecessor_qualifier='Z18',
            #                  section_name='Referenz auf die ID der Marktlokation'),
            #    '$["Dokument"][0]["Vorgang"]["0"]["Daten der Marktlokation"][0]["Referenz auf die ID der Marktlokation"]',
            #    id="Referenz auf die ID der Marktlokation"
            # )
            # pytest.param( # unsolved
            #    "utilmd_2379.xml",
            #    EdifactStackQuery(
            #        segment_group_key="SG6",
            #        segment_code="DTM",
            #        data_element_id="2379",
            #        name=None,
            #        predecessor_qualifier="752",
            #        section_name="Geplante Turnusablesung des MSB (Strom)",
            #    ),
            #    "$['foo']",
            #    id="UTILMD geplante Turnusablesung (Qualifier)",
            #    # https://github.com/Hochfrequenz/edifact-templates/issues/24
            # ),
        ],
    )
    def test_simple_paths(
        self,
        datafiles,
        mig_xml_path: str,
        query: EdifactStackQuery,
        expected_path: str,
    ):
        reader = MigXmlReader(Path(datafiles) / mig_xml_path)
        actual_stack = reader.get_edifact_stack(query)
        assert actual_stack is not None
        assert actual_stack.to_json_path() == expected_path  # type:ignore[union-attr]
