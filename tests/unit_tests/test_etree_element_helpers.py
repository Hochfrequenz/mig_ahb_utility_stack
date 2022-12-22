from typing import List, Literal, Optional

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]

from maus.reader.etree_element_helpers import get_ahb_name_or_none, get_nested_qualifiers, get_segment_group_key_or_none


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
        "xml_string, expected",
        [
            pytest.param('<foo ahbName="X"></foo>', "X"),
            pytest.param("<bar></bar>", None),
        ],
    )
    def test_get_ahb_name_or_none(self, xml_string: str, expected: Optional[str]):
        element = _string_to_element(xml_string)
        assert get_ahb_name_or_none(element) == expected

    @pytest.mark.parametrize(
        "ref_or_key, xml_string, expected",
        [
            pytest.param("ref", '<foo ref="hello"></foo>', None),
            pytest.param("ref", '<bar ref="NAD:2:0[1:0=MS]"></bar>', ["MS"]),
            pytest.param("ref", '<baz ref="RFF:1:1[RFF:1:0=Z13]"></baz>', ["Z13"]),
            pytest.param("ref", '<baz ref="DTM:1:1[1:0=469]"></baz>', ["469"]),
            pytest.param("key", '<baz asd="hello"></baz>', None),
            pytest.param("key", '<foo key="NAD:2:0[1:0=MS]"></foo>', ["MS"]),
            pytest.param("key", '<foo key="QTY:1:1[1:0=265|1:0=Z10|1:0=Z08]"></foo>', ["265", "Z10", "Z08"]),
            pytest.param("ref", '<field ref="FTX:4:(0,4)[1:0=ACB]" />', ["ACB"]),
            pytest.param("ref", '<field ref="CAV:1:0[CCI:1:0=Z02|CCI:1:0=Z04]" />', ["Z02", "Z04"]),
            pytest.param("key", '<class key="NAD:5:(0,3)[NAD:1:0=Z08]" ref="SG12" />', ["Z08"]),
            pytest.param("key", '<class key="NAD:4:(0,4)[NAD:1:0=Z07]" ref="SG12" />', ["Z07"]),
        ],
    )
    def test_get_nested_qualifier(self, ref_or_key: Literal["ref", "key"], xml_string: str, expected: List[str]):
        element = _string_to_element(xml_string)
        assert get_nested_qualifiers(ref_or_key, element) == expected
