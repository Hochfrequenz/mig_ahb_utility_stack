from typing import Optional

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]

from maus.reader.mig_ahb_name_helpers import are_similar_names, make_name_comparable, make_tree_names_comparable


class TestMigAhbNameHelpers:
    """
    Tests the behaviour of static helper methods
    """

    @pytest.mark.parametrize(
        "x,expected_result",
        [
            pytest.param("", ""),
            pytest.param(" foo", "foo", id="leading space"),
            pytest.param("foo ", "foo", id="trailing space"),
            pytest.param("Foo ", "foo", id="title case"),
            pytest.param("fOo ", "foo", id="mocking spongebob case"),
            pytest.param("🐈Miau ", "🐈miau", id="emoji"),
            pytest.param("Foo-Bar ", "foobar", id="minus"),
            pytest.param("Foo Bar ", "foobar", id="words"),
            pytest.param("Foo\nBar ", "foobar", id="new line"),
        ],
    )
    def test_make_name_comparable(self, x: str, expected_result: str):
        actual = make_name_comparable(x)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "x,y, expected_result",
        [
            pytest.param(None, "", True),
            pytest.param("", "", True),
            pytest.param("Foo", "", False),
            pytest.param(None, "Bar", False),
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
        actual = are_similar_names(x, y)
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
        make_tree_names_comparable(tree)
        for element in tree.iter():
            if "name" in element.attrib:
                assert element.attrib["name"] == make_name_comparable(element.attrib["name"])
            if "ahbName" in element.attrib:
                assert element.attrib["ahbName"] == make_name_comparable(element.attrib["ahbName"])
