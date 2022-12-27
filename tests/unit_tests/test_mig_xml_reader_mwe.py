from typing import Tuple

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]
from lxml.etree import Element  # type:ignore[import]

from maus.models.edifact_components import EdifactStack, EdifactStackLevel
from maus.navigation import AhbLocation, AhbLocationLayer
from maus.reader.mig_reader import MigXmlReader


class TestMigXmlReaderMwe:
    """
    Tests the behaviour of the Message Implementation Guide model with manually crafted minimal working examples.
    """

    # todo: you could probably use an indirect parametrization instead of the static helper methods below

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

    @staticmethod
    def _prepare_xml_reader_and_expected_element(xml_string: str, element_xpath: str) -> Tuple[MigXmlReader, Element]:
        """
        A helper method for easier test setup
        """
        reader = MigXmlReader(xml_string)
        elements = reader._original_tree.xpath(element_xpath)
        if len(elements) != 1:
            raise ValueError(
                f"In this test you're thought to provide an xpath that matches exactly one element of the given XML but found {len(elements)} for xpath '{element_xpath}'."
                # this means, the paths should be absolute
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
                '<?xml version="1.0"?><MSCONS><foo name="asd"><bar ahbName="qwe"/></foo></MSCONS>',
                "//MSCONS/foo/bar",
                False,
                EdifactStack.from_json_path(r'$["asd"]["qwe"]'),
            ),
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class name="asd"><bar ahbName="qwe"/></class></MSCONS>',
                "//MSCONS/class/bar",
                False,
                EdifactStack(
                    levels=[
                        EdifactStackLevel(name="asd", is_groupable=True),
                        EdifactStackLevel(name="qwe", is_groupable=False),
                    ]
                ),
            ),
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ahbName="asd"><bar name="qwe"/><class ahbName="opi"/></class></MSCONS>',
                "//MSCONS/class/class",
                False,
                EdifactStack(
                    levels=[
                        EdifactStackLevel(name="asd", is_groupable=True),
                        EdifactStackLevel(name="opi", is_groupable=True),
                    ]
                ),
            ),
            pytest.param(
                '<?xml version="1.0"?><UTILMD><class name="Dokument" ref="/" key="UNB:5:0"><class name="Absender_NAD" migName="MP-ID Absender" max="1" ref="SG2" key="NAD:2:0[1:0=MS]" ahbName="MP-ID Absender" meta.type="group" meta.objType="Marktpartner"></class></class></UTILMD>',
                "//UTILMD/class/class",
                False,
                EdifactStack(
                    levels=[
                        EdifactStackLevel(name="Dokument", is_groupable=True),
                        EdifactStackLevel(name="MP-ID Absender", is_groupable=True),
                        # "MP-ID Absender" shall be preferred over "Absender_NAD"
                    ]
                ),
            ),
            pytest.param(
                '<?xml version="1.0"?><UTILMD><class name="Dokument" ref="/" key="UNB:5:0"><class name="Nachricht" ref="UNH" key="UNH:1:0" max="9999" meta.type="group"><field name="Nachrichten-Referenznummer" ref="UNH:1:0" meta.id="0062" /><field name="Kategorie" migName="Beginn der Nachricht" meta.id="1001" ref="BGM:1:0" groupBy="Beginn der Nachricht" meta.help="Hier wird die Kategorie der gesamten Nachricht für alle Vorgänge angegeben." meta.type="repository" meta.typeInfo="Kategorierepository"/></class></class></UTILMD>',
                "//UTILMD/class/class/field[2]",
                False,
                EdifactStack(
                    levels=[
                        EdifactStackLevel(name="Dokument", is_groupable=True),
                        EdifactStackLevel(name="Nachricht", is_groupable=True),
                        EdifactStackLevel(name="Kategorie", is_groupable=False),
                    ]
                ),
            ),
        ],
    )
    def test_element_to_edifact_stack(
        self, xml_string: str, element_xpath: str, use_sanitized: bool, expected_result: EdifactStack
    ):
        reader, element = TestMigXmlReaderMwe._prepare_xml_reader_and_element(xml_string, element_xpath)
        actual = reader.element_to_edifact_stack(element, use_sanitized_tree=use_sanitized)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string,ahb_location,expected_result_xpath",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="/"><class ref="UNH"><class ref="SG1"><foo/></class></class></class></MSCONS>',
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key=None, opening_segment_code="UNH", opening_qualifier=None),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="FOO", opening_qualifier="BAR"),
                    ]
                ),
                "/MSCONS/class/class/class",
                id="simple unique result",
            ),
            pytest.param(
                '<?xml version="1.0"?><UTILMD><class ref="/"><class ref="UNH"><class ref="SG4" key="IDE:2:0"><class name="Netznutzungsabrechnungsdaten der Marktlokation" ref="SG8" key="SEQ:1:0[SEQ:1:0=Z45]"><foo/></class><class name="Weitere Abrechnungsdaten der Marktlokation" ref="SG8" key="SEQ:1:0[SEQ:1:0=Z46]"><field name="ID" ref="PIA:2:0[PIA:1:0=Z02]" meta.id="7140" /></class></class></class></class></UTILMD>',
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key=None, opening_segment_code="UNH", opening_qualifier=None),
                        AhbLocationLayer(segment_group_key="SG4", opening_segment_code="IDE", opening_qualifier="24"),
                        AhbLocationLayer(segment_group_key="SG8", opening_segment_code="SEQ", opening_qualifier="Z46"),
                    ],
                    data_element_id="7140",
                ),
                "/UTILMD/class/class/class/class[2]/field",
                id="distinguish by sg key, then by data element",
            ),
            pytest.param(
                '<?xml version="1.0"?><UTILMD><class ref="/"><class ref="UNH"><class ref="SG4" key="IDE:2:0"><field name="Vertragsbeginn" ref="DTM:1:1[1:0=92]" meta.format="102" meta.id="2380" meta.type="date-time" ahbName="Beginn zum" /><field name="Vertragsende" ref="DTM:1:1[1:0=93]" meta.format="102" meta.id="2380" ahbName="Ende zum" meta.type="date-time" /></class></class></class></UTILMD>',
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key=None, opening_segment_code="UNH", opening_qualifier=None),
                        AhbLocationLayer(segment_group_key="SG4", opening_segment_code="IDE", opening_qualifier="24"),
                    ],
                    data_element_id="2380",
                    qualifier="93",
                ),
                "/UTILMD/class/class/class/field[2]",
                id="DTM92 and DTM93",
            ),
        ],
    )
    def test_get_segment_group_element(self, xml_string: str, ahb_location: AhbLocation, expected_result_xpath: str):
        reader, expected_element = TestMigXmlReaderMwe._prepare_xml_reader_and_expected_element(
            xml_string, expected_result_xpath
        )
        actual = reader.get_element(ahb_location=ahb_location)
        assert actual == expected_element
