"""
contains the MigXmlReader - a MIG Reader that is based on XML MIGs (and therefore requires lxml)
"""

import re
from pathlib import Path
from typing import List, Set, TypeVar, Union, Optional
from xml.etree.ElementTree import Element

from maus.reader.ahb_location_xml import from_xml_elements

try:
    from lxml import etree  # type:ignore[import]
except ImportError as import_error:
    import_error.msg += "; Did you install maus[xml]?"
    # lxml is only an optional dependency of maus but in this module, it is required
    raise

from more_itertools import first, one

from maus.edifact import EdifactFormat
from maus.models.edifact_components import EdifactStack, EdifactStackLevel
from maus.models.message_implementation_guide import SegmentGroupHierarchy
from maus.navigation import AhbLocation, AhbLocationLayer
from maus.reader.etree_element_helpers import get_nested_qualifiers
from maus.reader.mig_ahb_name_helpers import make_tree_names_comparable
from maus.reader.mig_reader import MigReader

Result = TypeVar("Result")  #: is a type var to indicate an "arbitrary but same" type in a generic function


def check_file_can_be_parsed_as_mig_xml(file_path: Path) -> None:
    """
    Returns nothing iff the given file is parsable as XML and contains no obvious errors.
    This is not a really sophisticated analysis but just a basic minimal sanity check.
    In case of error an exception is raised.
    """
    reader = MigXmlReader(file_path)
    _ = EdifactFormat(reader.get_format_name())  # dies with an exception if the value is invalid


# pylint:disable=c-extension-no-member
class MigXmlReader(MigReader):
    """
    Reads an XML file and transforms it into a Segment Group Hierarchy
    """

    _pipe_separated_names_with_digit_suffix_pattern = re.compile(
        r"^(?P<name_without_suffix>[\w\s]+)(?P<names_with_suffix>(?:\|\1\d+)+)$"
    )
    """
    https://regex101.com/r/wg5Fs5/1
    """

    def __init__(self, init_param: Union[str, Path]):
        self._original_root: etree._Element
        if isinstance(init_param, str):
            self._original_root = etree.fromstring(init_param)
            self._sanitized_root = etree.fromstring(init_param)
        elif isinstance(init_param, Path):
            self._original_root = etree.parse(str(init_param.absolute())).getroot()
            self._sanitized_root = etree.parse(str(init_param.absolute())).getroot()
        else:
            raise ValueError(f"The type of '{init_param}' is not valid")
        # self._unpack_virtual_groups() # check if this is needed at some point in the future; I don't know yet
        # the original tree is the unmodified MIG XML Structure with all its quircks
        self._original_tree: etree.ElementTree = etree.ElementTree(self._original_root)
        # but turns out, it's much easier to handle a sanitized tree that is simplified in a sense that
        # * has only lower case (ahb)names which are easy to match because they don't contain whitespace,"-" or casing
        # * has the same structure as the _original_tree so that absolute path expressions from the sanitized tree match
        self._sanitized_tree: etree.ElementTree = etree.ElementTree(self._sanitized_root)
        make_tree_names_comparable(self._sanitized_tree)

    def _unpack_virtual_groups(self) -> None:
        """
        unpacks groups with @meta.virtual="true".
        Any <root><group meta.virtual="true"><foo/><bar/></group></root> will be unpacked and modify the root to
        <root><foo/><bar/></root>
        :return:
        """
        elements_that_have_foo_groups = self._original_root.xpath('//class[@meta.virtual="true"]/parent::*')
        for element_that_has_foo_groups in elements_that_have_foo_groups:
            for foo_group in element_that_has_foo_groups.xpath('./class[@meta.virtual="true"]'):
                foo_group_index = element_that_has_foo_groups.index(foo_group)
                for foo_field in foo_group:
                    element_that_has_foo_groups.insert(foo_group_index - 1, foo_field)
                element_that_has_foo_groups.remove(foo_group)

    def get_format_name(self) -> str:
        """
        the root element of the XML is the name of the EDIFACT format
        """
        return self._original_root.tag

    def element_to_edifact_stack(self, element: etree.Element, use_sanitized_tree: bool) -> EdifactStack:
        """
        extract the edifact seed path from the given element.
        """
        # this method is directly unittests. Please refer to the test for some easy to debug examples.
        if use_sanitized_tree:
            xpath = self._sanitized_tree.getpath(element)
        else:
            xpath = self._original_tree.getpath(element)
        stack = EdifactStack(levels=[])
        iter_path = "/" + xpath.split("/")[1]
        for leaf in xpath.split("/")[2:]:
            iter_path += "/" + leaf
            # here we _always_ need to use the original root!
            leaf_element = self._original_root.xpath(iter_path)[0]  # type:ignore[attr-defined]
            level_name: str
            # todo: maybe skip virtual groups
            is_groupable = leaf_element.tag == "class"
            attribute_keys_sorted_by_priority: List[str]
            if is_groupable:
                attribute_keys_sorted_by_priority = ["migName", "ahbName", "name"]
            else:
                # I didn't create the data. I'm just trying to cope with it...
                attribute_keys_sorted_by_priority = ["ahbName", "name", "migName"]
            for attribute_key in attribute_keys_sorted_by_priority:
                if attribute_key in leaf_element.attrib:
                    level_name = leaf_element.attrib[attribute_key]
                    break
            # https://stackoverflow.com/questions/47972143/using-attr-with-pylint
            # pylint: disable=no-member
            stack.levels.append(EdifactStackLevel(name=level_name, is_groupable=is_groupable))
        return stack

    def _get_candidate_index_from_key(self, layer: AhbLocationLayer, candidates: List[Element]) -> int:
        key_set: Set[str]
        possible_results: List[int] = []
        for candidate_index, key_set in enumerate(
            set(get_nested_qualifiers("key", candidate) or []) for candidate in candidates
        ):
            if layer.opening_qualifier in key_set:
                possible_results.append(candidate_index)
        if len(possible_results) == 0:
            raise ValueError(f"Couldn't find any candidate with opening_qualifier '{layer.opening_qualifier}'")
        # todo: what if there are >1 matches. using the first one just hides data problems. we should use one instead
        return first(possible_results)

    def _find_element_using_explicit_location(self, ahb_location: AhbLocation) -> Optional[Element]:
        """
        find the perfect match, if it exists
        :param ahb_location:
        :return: None if no perfect match was found; the perfect match otherwise
        """
        all_explicit_locations = self._original_tree.xpath(f"//ahbLocations")
        location_layers_only = AhbLocation(
            layers=ahb_location.layers, data_element_id=None, qualifier=None
        )
        for explicit_locations in all_explicit_locations:
            locations_from_mig_xml = from_xml_elements(explicit_locations)
            for location_from_mig_xml in locations_from_mig_xml:
                location_layers_from_mig_xml = AhbLocation(
                    layers=location_from_mig_xml.layers, data_element_id=None, qualifier=None
                )
                if ahb_location==location_from_mig_xml or (location_layers_only==location_layers_from_mig_xml and ahb_location.data_element_id is None):
                    result = explicit_locations.getparent()
                    if ahb_location.data_element_id is None:
                        while result.tag!="class":
                            result = result.getparent()
                    return result
        return None


    # First make it work, then split it up
    # pylint:disable=too-many-branches
    def get_element(self, ahb_location: AhbLocation) -> Element:
        """
        Finds and returns the segment group for the specified location.
        Raises ValueErrors if it cannot find the group or the result would be ambiguous.
        """
        candidates: List[Element]
        if (perfect_match := self._find_element_using_explicit_location(ahb_location)) is not None:
            return perfect_match
        final_query_path = f"/{self.get_format_name()}/class[@ref='/']"
        for layer in ahb_location.layers:
            query_path = final_query_path + f"/class[@ref='{layer.segment_group_key or 'UNH'}']"
            candidates = list(self._original_root.xpath(query_path))
            if len(candidates) == 0:
                raise ValueError(f"No element found for path {query_path}")
            if len(candidates) > 1:
                candidate_index = self._get_candidate_index_from_key(layer, candidates)
                final_query_path = query_path + f"[{candidate_index + 1}]"  # xpath index starts at 1, not 0
                candidates = [candidates[candidate_index]]  # list must only contain 1 remaining item at this point
                continue
            final_query_path = query_path
        if ahb_location.segment_code is not None and ahb_location.segment_code != "UNH":
            # if there is a separate class for the segment, handle it here... is most cases it's not
            query_path = final_query_path + f"/class[@ref='{ahb_location.segment_code}']"
            segment_candidates = list(self._original_root.xpath(query_path))
            if len(segment_candidates) > 1:
                for candidate_index, key_set in enumerate(
                    set(get_nested_qualifiers("key", candidate) or []) for candidate in segment_candidates
                ):
                    # if layer is undefined here, we got other problems; it's ok to crash
                    if layer.opening_qualifier in key_set:  # pylint:disable=undefined-loop-variable
                        final_query_path = query_path + f"[{candidate_index + 1}]"  # xpath index starts at 1, not 0
                        candidates = segment_candidates
                        break
            elif len(segment_candidates) == 1:
                final_query_path = query_path
        if ahb_location.data_element_id is not None:
            # now inside the remaining segment group find the entry that has the correct data element id
            query_path = final_query_path + f"/field[@meta.id='{ahb_location.data_element_id}']"  # todo:virtual groups
            candidates = list(self._original_root.xpath(query_path))
            if len(candidates) == 0:
                # todo: go a level up
                raise ValueError(f"No element found for path {query_path}")
            if len(candidates) > 1:
                if ahb_location.qualifier is not None:
                    candidate_index = one(
                        (
                            n
                            for n, c in enumerate(candidates)
                            if ahb_location.qualifier in set(get_nested_qualifiers("ref", c) or [])
                        ),
                        too_short=ValueError(f"Couldn't find any candidate with ref '{ahb_location.qualifier}'"),
                    )
                    final_query_path = query_path + f"[{candidate_index + 1}]"
                    candidates = candidates[candidate_index : candidate_index + 1]
                else:
                    raise ValueError(
                        f"Couldn't find a unique candidate with data element id '{ahb_location.data_element_id}'"
                    )
        return one(candidates)

    def get_edifact_stack(self, location: AhbLocation) -> EdifactStack:
        """
        get the edifact stack for the given segment_group, segment... combination or None if there is no match
        """
        element = self.get_element(location)
        return self.element_to_edifact_stack(element, use_sanitized_tree=False)

    def to_segment_group_hierarchy(self) -> SegmentGroupHierarchy:
        """
        convert the read data into a segment group hierarchy
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")
