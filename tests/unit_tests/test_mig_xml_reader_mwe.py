from typing import List, Optional, Tuple

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]
from lxml.etree import Element  # type:ignore[import]

from maus.models._internal import MigFilterResult
from maus.models.edifact_components import EdifactStack, EdifactStackLevel, EdifactStackQuery
from maus.reader.etree_element_helpers import list_to_mig_filter_result
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
    def _prepare_xml_reader_and_elements(
        xml_string: str, elements_xpathes: List[str]
    ) -> Tuple[MigXmlReader, List[Element]]:
        """
        A helper method for easier test setup
        """
        reader = MigXmlReader(xml_string)
        result_elements: List[Element] = []
        for xpath in elements_xpathes:
            elements = reader._original_tree.xpath(xpath)
            if len(elements) != 1:
                raise ValueError(
                    f"In this test you're thought to provide an xpath that matches exactly one element of the given XML but found {len(elements)} for xpath '{xpath}'."
                    # this means, the paths should be absolute
                )
            element = elements[0]
            result_elements.append(element)
        return reader, result_elements

    @staticmethod
    def _prepare_mig_filter_result(tree: etree.ElementTree, elements_xpathes: List[str]) -> MigFilterResult:
        """
        A helper method for easier test setup. It basically re-implements "get_unique_result_by_xpath"
        """
        results: List[Element] = []
        for xpath in elements_xpathes:
            elements = tree.xpath(xpath)
            if len(elements) != 1:
                raise ValueError(
                    f"In this test you're thought to provide an xpath that matches exactly one element of the given XML but found {len(elements)} for xpath '{xpath}'."
                )
            element = elements[0]
            results.append(element)
        return list_to_mig_filter_result(results)

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
        reader, element = TestMigXmlReaderMwe._prepare_xml_reader_and_element(xml_string, element_xpath)
        actual = reader.get_parent_segment_group_key(element, use_sanitized_tree=use_sanitized)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string, element_xpath, use_sanitized, expected_result",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><foo key="DTM:1:2[1:0=Z21]"><bar/></foo></MSCONS>',
                "//MSCONS/foo/bar",
                False,
                ["Z21"],
                id="single predecessor",
            ),
            pytest.param(
                '<?xml version="1.0"?><UTILMD><class key="QTY:1:1[1:0=265|1:0=Z10|1:0=Z08]"><field /></class></UTILMD>',
                "//UTILMD/class/field",
                False,
                ["265", "Z10", "Z08"],
                id="multiple predecessors",
            ),
        ],
    )
    def test_get_parent_predecessors(
        self, xml_string: str, element_xpath: str, use_sanitized: bool, expected_result: List[str]
    ):
        reader, element = TestMigXmlReaderMwe._prepare_xml_reader_and_element(xml_string, element_xpath)
        actual = reader.get_parent_predecessors(element, use_sanitized_tree=use_sanitized)
        assert actual == expected_result

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
        ],
    )
    def test_element_to_edifact_stack(
        self, xml_string: str, element_xpath: str, use_sanitized: bool, expected_result: EdifactStack
    ):
        reader, element = TestMigXmlReaderMwe._prepare_xml_reader_and_element(xml_string, element_xpath)
        actual = reader.element_to_edifact_stack(element, use_sanitized_tree=use_sanitized)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string,candidates_xpaths,query,expected_result_xpaths",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42"><foo/></class></MSCONS>',
                ["//MSCONS/class/foo"],
                EdifactStackQuery(
                    segment_group_key="SG42",
                    segment_code="XXX",
                    data_element_id="0000",
                    name="",
                ),
                ["//MSCONS/class/foo"],
            ),
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42"><foo/></class></MSCONS>',
                ["//MSCONS/class/foo"],
                EdifactStackQuery(
                    segment_group_key="SG17",
                    segment_code="XXX",
                    data_element_id="0000",
                    name="",
                ),
                [],
            ),
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42"><foo/><bar/></class></MSCONS>',
                ["//MSCONS/class/foo", "//MSCONS/class/bar"],
                EdifactStackQuery(
                    segment_group_key="SG42",
                    segment_code="XXX",
                    data_element_id="0000",
                    name="",
                ),
                ["//MSCONS/class/foo", "//MSCONS/class/bar"],
            ),
        ],
    )
    def test_get_unique_result_by_segment_group(
        self, xml_string: str, candidates_xpaths: List[str], query: EdifactStackQuery, expected_result_xpaths: List[str]
    ):
        reader, candidates = TestMigXmlReaderMwe._prepare_xml_reader_and_elements(xml_string, candidates_xpaths)
        expected_result = TestMigXmlReaderMwe._prepare_mig_filter_result(reader._original_tree, expected_result_xpaths)
        actual = reader.get_unique_result_by_segment_group(candidates=candidates, query=query, use_sanitized_tree=False)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string,candidates_xpaths,query,expected_result_xpaths",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42"><foo/></class><class ref="SG77"><bar/></class></MSCONS>',
                ["//MSCONS/class/foo", "//MSCONS/class/bar"],
                EdifactStackQuery(
                    segment_group_key="SG42",
                    segment_code="XXX",  # dummy
                    data_element_id="0000",  # dummy
                    name="",
                ),
                ["//MSCONS/class/foo"],
            ),
        ],
    )
    def test_get_unique_result_by_parent_segment_group(
        self, xml_string: str, candidates_xpaths: List[str], query: EdifactStackQuery, expected_result_xpaths: List[str]
    ):
        reader, candidates = TestMigXmlReaderMwe._prepare_xml_reader_and_elements(xml_string, candidates_xpaths)
        expected_result = TestMigXmlReaderMwe._prepare_mig_filter_result(reader._original_tree, expected_result_xpaths)
        actual = reader.get_unique_result_by_parent_segment_group(candidates=candidates, query=query)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string,candidates_xpaths,query,expected_result_xpaths",
        [
            pytest.param(
                '<?xml version="1.0"?><REQOTE><class ahbName="MP-ID Absender"><foo/></class><class ahbName="MP-ID Empfänger"><bar/></class></REQOTE>',
                ["//REQOTE/class/foo", "//REQOTE/class/bar"],
                EdifactStackQuery(
                    segment_group_key="SG42",  # dummy
                    segment_code="XXX",  # dummy
                    data_element_id="0000",  # dummy
                    name="",
                    section_name="MP-ID Absender",
                ),
                ["//REQOTE/class/foo"],
            ),
        ],
    )
    def test_get_unique_result_by_parent_ahb_name_section_name(
        self, xml_string: str, candidates_xpaths: List[str], query: EdifactStackQuery, expected_result_xpaths: List[str]
    ):
        reader, candidates = TestMigXmlReaderMwe._prepare_xml_reader_and_elements(xml_string, candidates_xpaths)
        expected_result = TestMigXmlReaderMwe._prepare_mig_filter_result(reader._original_tree, expected_result_xpaths)
        actual = reader.get_unique_result_by_parent_ahb_name_section_name(candidates=candidates, query=query)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string,candidates_xpaths,query,expected_result_xpaths",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42"><foo name="hello"/><bar name="world"/></class></MSCONS>',
                ["//MSCONS/class/foo", "//MSCONS/class/bar"],
                EdifactStackQuery(
                    segment_group_key="SG123",  # dummy
                    segment_code="XXX",  # dummy
                    data_element_id="0000",  # dummy
                    name="world",
                ),
                ["//MSCONS/class/bar"],
            ),
        ],
    )
    def test_get_unique_result_by_name(
        self, xml_string: str, candidates_xpaths: List[str], query: EdifactStackQuery, expected_result_xpaths: List[str]
    ):
        reader, candidates = TestMigXmlReaderMwe._prepare_xml_reader_and_elements(xml_string, candidates_xpaths)
        expected_result = TestMigXmlReaderMwe._prepare_mig_filter_result(reader._original_tree, expected_result_xpaths)
        actual = reader.get_unique_result_by_name(candidates=candidates, query=query)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string,candidates_xpaths,query,expected_result_xpaths",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42" name="foo"><x name="xx"/><y name="yy"/></class></MSCONS>',
                ["//MSCONS/class/x", "//MSCONS/class/y", "//MSCONS/class/y"],
                EdifactStackQuery(
                    segment_group_key="SG123",  # dummy
                    segment_code="XXX",  # dummy
                    data_element_id="0000",  # dummy
                    name="asd",  # dummy
                    section_name="xx",
                ),
                ["//MSCONS/class/x"],
            ),
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42" name="foo"><x name="XxX"/><y name="yy"/></class></MSCONS>',
                ["//MSCONS/class/x", "//MSCONS/class/y", "//MSCONS/class/y"],
                EdifactStackQuery(
                    segment_group_key="SG123",  # dummy
                    segment_code="XXX",  # dummy
                    data_element_id="0000",  # dummy
                    name="asd",  # dummy
                    section_name="xxx",
                ),
                ["//MSCONS/class/x"],
            ),
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG42" name="foo"><x name=" XxX-"/><y name="yy"/></class></MSCONS>',
                ["//MSCONS/class/x", "//MSCONS/class/y", "//MSCONS/class/y"],
                EdifactStackQuery(
                    segment_group_key="SG123",  # dummy
                    segment_code="XXX",  # dummy
                    data_element_id="0000",  # dummy
                    name="asd",  # dummy
                    section_name="xxx",
                ),
                ["//MSCONS/class/x"],
            ),
        ],
    )
    def test_get_unique_result_by_section_name(
        self, xml_string: str, candidates_xpaths: List[str], query: EdifactStackQuery, expected_result_xpaths: List[str]
    ):
        reader, candidates = TestMigXmlReaderMwe._prepare_xml_reader_and_elements(xml_string, candidates_xpaths)
        expected_result = TestMigXmlReaderMwe._prepare_mig_filter_result(reader._original_tree, expected_result_xpaths)
        actual = reader.get_unique_result_by_section_name(candidates=candidates, query=query)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string,candidates_xpaths,query,expected_result_xpaths",
        [
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class ref="SG1" key="RFF:1:1[RFF:1:0=AGI]"><foo/></class></MSCONS>',
                ["//MSCONS/class"],
                EdifactStackQuery(
                    segment_group_key="SG1",
                    segment_code="RFF",
                    predecessor_qualifier="AGI",
                    data_element_id="0000",  # dummy
                    name="",  # dummy
                ),
                ["//MSCONS/class"],
                id="rffuck1 mit ref",
            ),
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class><foo key="RFF:1:1[RFF:1:0=AGI]"/></class></MSCONS>',
                ["//MSCONS/class/foo"],
                EdifactStackQuery(
                    segment_group_key="SG1",
                    segment_code="RFF",
                    predecessor_qualifier="AGI",
                    data_element_id="0000",  # dummy
                    name="",  # dummy
                ),
                ["//MSCONS/class/foo"],
                id="rffuck2 mit key",
            ),
            pytest.param(
                '<?xml version="1.0"?><MSCONS><class><foo ref="DTM:1:1[1:0=Z21]"/></class></MSCONS>',
                ["//MSCONS/class/foo"],
                EdifactStackQuery(
                    segment_group_key="SG1",
                    segment_code="DTM",
                    predecessor_qualifier="Z21",
                    data_element_id="0000",  # dummy
                    name="",  # dummy
                ),
                ["//MSCONS/class/foo"],
                id="dtm",
            ),
        ],
    )
    def test_get_unique_result_by_predecessor(
        self, xml_string: str, candidates_xpaths: List[str], query: EdifactStackQuery, expected_result_xpaths: List[str]
    ):
        reader, candidates = TestMigXmlReaderMwe._prepare_xml_reader_and_elements(xml_string, candidates_xpaths)
        expected_result = TestMigXmlReaderMwe._prepare_mig_filter_result(reader._original_tree, expected_result_xpaths)
        actual = reader.get_unique_result_by_predecessor(candidates=candidates, query=query)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "xml_string,candidates_xpaths,query,expected_result_xpaths",
        [
            pytest.param(
                '<?xml version="1.0"?><UTILMD><class key="LOC:2:0[1:0=Z08]"><field ref="LOC:2:0"/></class></UTILMD>',
                ["//UTILMD/class/field"],
                EdifactStackQuery(
                    segment_group_key="SG1",  # dummy
                    segment_code="LOC",
                    predecessor_qualifier="Z08",
                    data_element_id="0000",  # dummy
                    name="",  # dummy
                ),
                ["//UTILMD/class/field"],
                id="loc",
            ),
        ],
    )
    def test_get_unique_result_by_parent_predecessor(
        self, xml_string: str, candidates_xpaths: List[str], query: EdifactStackQuery, expected_result_xpaths: List[str]
    ):
        reader, candidates = TestMigXmlReaderMwe._prepare_xml_reader_and_elements(xml_string, candidates_xpaths)
        expected_result = TestMigXmlReaderMwe._prepare_mig_filter_result(reader._original_tree, expected_result_xpaths)
        actual = reader.get_unique_result_by_parent_predecessor(candidates=candidates, query=query)
        assert actual == expected_result
