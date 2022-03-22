"""
This module contains (static) functions that process single lxml.etree Elements.
Each function is separately unit tested.
"""
import re
from typing import List, Literal, Optional

# pylint:disable=no-name-in-module
from lxml.etree import Element  # type:ignore[import]

from maus.models._internal import MigFilterResult
from maus.models.edifact_components import EdifactStackQuery
from maus.reader.mig_ahb_name_helpers import are_similar_names


def get_segment_group_key_or_none(element: Element) -> Optional[str]:
    """
    returns the segment group of element if present; None otherwise
    """
    if "ref" in element.attrib and element.attrib["ref"].startswith("SG"):
        # the trivial case
        return element.attrib["ref"]
    return None


#: a regex to match a ref-segment: https://regex101.com/r/KY25AH/1
_nested_qualifier_pattern = re.compile(r"^(?P<segment_code>[A-Z]+):\d+:\d+\[(?:\w+:)+\w+:?=(?P<qualifier>[A-Z\d]+)\]$")


def get_nested_qualifier(attrib_key: Literal["ref", "key"], element: Element) -> Optional[str]:
    """
    returns the nested qualifier of an element if present; None otherwise
    """
    if attrib_key in element.attrib:
        match = _nested_qualifier_pattern.match(element.attrib[attrib_key])
        if match:
            return match["qualifier"]
    return None


def filter_by_name(candidates: List[Element], query: EdifactStackQuery) -> List[Element]:
    """
    returns those elements that have the given name (in the query)
    """
    filtered_by_names = [
        x
        for x in candidates
        if are_similar_names(x.attrib["name"], query.name)
        or ("ahbName" in x.attrib and are_similar_names(x.attrib["ahbName"], query.name))
    ]
    return filtered_by_names


def filter_by_section_name(candidates: List[Element], query: EdifactStackQuery) -> List[Element]:
    """
    returns those elements that have the given section name (in the query)
    """
    filtered_by_names = [x for x in candidates if are_similar_names(x.attrib["name"], query.section_name)]
    return filtered_by_names


def list_to_mig_filter_result(candidates: List[Element]) -> MigFilterResult:
    """
    uses a given list of elements and differentiates three cases:
    1. the list contains a single unique element
    2. the list contains multiple elements
    3. the list contains no elements at all
    """
    if len(candidates) == 0:
        return MigFilterResult(candidates=None, is_unique=None, unique_result=None)
        # the == 1 case is handled last
    if len(candidates) > 1:
        return MigFilterResult(candidates=candidates, is_unique=False, unique_result=None)
    return MigFilterResult(candidates=None, is_unique=True, unique_result=candidates[0])
