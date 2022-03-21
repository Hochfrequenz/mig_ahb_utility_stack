from typing import Literal, Optional

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]

from maus.reader.etree_element_helpers import get_nested_qualifier, get_segment_group_key_or_none


def _string_to_element(xml_elem: str) -> etree.Element:
    """
    helper method that adds an XML preamble to the given string, parses the concatenated string as etree
    and returns the root element
    """
    valid_xml = '<?xml version="1.0"?>' + xml_elem
    root = etree.fromstring(valid_xml)
    return root


class TestEtreeElementHelpers:
    """
    Tests the behaviour of static helper methods
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
