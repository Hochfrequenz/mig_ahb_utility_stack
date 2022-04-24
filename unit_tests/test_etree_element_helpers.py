from typing import List, Literal, Optional

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]

from maus.models.edifact_components import EdifactStackQuery
from maus.reader.etree_element_helpers import (
    filter_by_name,
    filter_by_section_name,
    get_nested_qualifier,
    get_segment_group_key_or_none,
    list_to_mig_filter_result,
)


def _string_to_element(xml_elem: str) -> etree.Element:
    """
    helper method that adds an XML preamble to the given string, parses the concatenated string as etree
    and returns the root element
    """
    valid_xml = '<?xml version="1.0"?>' + xml_elem
    root = etree.fromstring(valid_xml)
    return root


def _string_to_elements(xml_elem: str) -> List[etree.Element]:
    """
    helper method that adds an XML preamble and virtual root to the given string,
    parses the concatenated string as etree and returns the elements on root level
    """
    valid_xml = '<?xml version="1.0"?><virtual_root>' + xml_elem + "</virtual_root>"
    root = etree.fromstring(valid_xml)
    return [x for x in root.findall("./")]


class TestEtreeSingleElementHelpers:
    """
    Tests the behaviour of static helper methods (for single elements)
    """

    @pytest.mark.parametrize(
        "xml_string, expected",
        [
            pytest.param('<foo ref="SG14"></foo>', "SG14"),
            pytest.param("<bar></bar>", None),
        ],
    )
    def test_get_segment_group_key_or_none(self, xml_string: str, expected: Optional[str]):
        element = _string_to_element(xml_string)
        assert get_segment_group_key_or_none(element) == expected

    @pytest.mark.parametrize(
        "ref_or_key, xml_string, expected",
        [
            pytest.param("ref", '<foo ref="hello"></foo>', None),
            pytest.param("ref", '<bar ref="NAD:2:0[1:0=MS]"></bar>', "MS"),
            pytest.param("ref", '<baz ref="RFF:1:1[RFF:1:0=Z13]"></baz>', "Z13"),
            pytest.param("ref", '<baz ref="DTM:1:1[1:0=469]"></baz>', "469"),
            pytest.param("key", '<baz asd="hello"></baz>', None),
            pytest.param("key", '<foo key="NAD:2:0[1:0=MS]"></foo>', "MS"),
        ],
    )
    def test_get_nested_qualifier(self, ref_or_key: Literal["ref", "key"], xml_string: str, expected: Optional[str]):
        element = _string_to_element(xml_string)
        assert get_nested_qualifier(ref_or_key, element) == expected


class TestMultipleElementsHelpers:
    """
    Tests the behaviour of static helper methods (for multiple elements)
    """

    @pytest.mark.parametrize(
        "xml_string,expected_is_unique, expected_has_unique_result, expected_candidates_length",
        [
            pytest.param(
                "<bar/><baz/><foo/>",
                False,
                None,
                3,
            ),
            pytest.param(
                "<bar/>",
                True,
                True,
                None,
            ),
            pytest.param(
                "",
                None,
                False,
                None,
            ),
        ],
    )
    def test_list_to_mig_filter_result(
        self,
        xml_string: str,
        expected_is_unique: Optional[bool],
        expected_has_unique_result: bool,
        expected_candidates_length: Optional[int],
    ):
        elements = _string_to_elements(xml_string)
        actual = list_to_mig_filter_result(elements)
        assert actual.is_unique is expected_is_unique
        if expected_is_unique:
            assert actual.unique_result is not None
        else:
            assert actual.unique_result is None
        if expected_candidates_length is not None:
            assert actual.candidates is not None
            assert len(actual.candidates) == expected_candidates_length
        else:
            assert actual.candidates is None

    @pytest.mark.parametrize(
        "xml_string, query, expected_allowed_ids",
        [
            pytest.param(
                '<bar name="foo" id="this"></bar><baz name="fuu" id="that"/>',
                EdifactStackQuery(
                    segment_group_key="SG1",
                    segment_code="ASD",
                    data_element_id="1234",
                    name="foo",
                    predecessor_qualifier=None,
                ),
                ["this"],
            ),
            pytest.param(
                '<bar name="bar" id="this"></bar><baz name=" Foo-" id="that"/>',
                EdifactStackQuery(
                    segment_group_key="SG1",
                    segment_code="ASD",
                    data_element_id="1234",
                    name="foo",
                    predecessor_qualifier=None,
                ),
                ["that"],
            ),
            pytest.param(
                '<bar name="bar" id="this"></bar><baz name="something" ahbName=" Foo-" id="that"/>',
                EdifactStackQuery(
                    segment_group_key="SG1",
                    segment_code="ASD",
                    data_element_id="1234",
                    name="foo",
                    predecessor_qualifier=None,
                ),
                ["that"],
            ),
        ],
    )
    def test_filter_by_name(self, xml_string: str, query: EdifactStackQuery, expected_allowed_ids: List[str]):
        elements = _string_to_elements(xml_string)
        actual = filter_by_name(elements, query)
        assert [x.attrib["id"] for x in actual] == expected_allowed_ids

    @pytest.mark.parametrize(
        "xml_string, query, expected_allowed_ids",
        [
            pytest.param(
                '<bar name="foo" id="this"></bar><baz name="fuu" id="that"/>',
                EdifactStackQuery(
                    segment_group_key="SG12",
                    section_name="Foo",
                    segment_code="ASD",
                    data_element_id="1234",
                    name="asd",
                    predecessor_qualifier=None,
                ),
                ["this"],
            ),
            pytest.param(
                '<bar name="hello" id="this"></bar><baz name=" Foo-" id="that"/>',
                EdifactStackQuery(
                    segment_group_key="Foo",
                    section_name="Hello",
                    segment_code="ASD",
                    data_element_id="1234",
                    name="asd",
                    predecessor_qualifier=None,
                ),
                ["this"],
            ),
            pytest.param(
                '<bar name="hello" id="this"></bar><baz name="HeLlO" id="that"/>',
                EdifactStackQuery(
                    segment_group_key="Foo",
                    section_name="Hello",
                    segment_code="ASD",
                    data_element_id="1234",
                    name="asd",
                    predecessor_qualifier=None,
                ),
                ["this", "that"],
            ),
        ],
    )
    def test_filter_by_section_name(self, xml_string: str, query: EdifactStackQuery, expected_allowed_ids: List[str]):
        elements = _string_to_elements(xml_string)
        actual = filter_by_section_name(elements, query)
        assert [x.attrib["id"] for x in actual] == expected_allowed_ids
