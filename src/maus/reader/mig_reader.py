"""
Classes that allow to read XML files that contain structural information (Message Implementation Guide information)
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union
from xml.etree.ElementTree import Element

import attr
from lxml import etree  # type:ignore[import]

from maus import SegmentGroupHierarchy
from maus.models.edifact_components import EdifactStack, EdifactStackLevel


class MigReader(ABC):
    """
    A MIG reader is a class that reads Message Implementation Guide (MIG) data from a source
    """

    @abstractmethod
    def to_segment_group_hierarchy(self) -> SegmentGroupHierarchy:
        """
        convert the read data into a segment group hierarchy
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")

    @staticmethod
    def are_similar_names(name_x: Optional[str], name_y: Optional[str]) -> bool:
        """
        Returns true if name_x and name_y are somehow similar.
        "Somehow similar" in this context means, that all the artefacts from text to word to PDF + scraping
        + human errors might add up to something which explains the difference between name_x and name_y.
        """
        if (name_x and not name_y) or (name_y and not name_x):
            return False
        if (not name_x) and (not name_y):
            return True
        # neither name_x nor name_y are None below this line
        return MigReader.make_name_comparable(name_x) == MigReader.make_name_comparable(name_y)  # type:ignore[arg-type]

    @staticmethod
    def make_name_comparable(orig_str: str) -> str:
        """
        Removes all the characters that could be a problem when matching names from the AHB with names from the MIG
        """
        result: str = orig_str.lower()
        for removable_character in [" ", "-", "\n"]:
            result = result.replace(removable_character, "")
        return result

    @staticmethod
    def make_tree_names_comparable(tree: etree.ElementTree) -> None:  # pylint:disable=c-extension-no-member
        """
        modifies the provided tree by applying `make_name_comparable` to all name and ahbName attributes
        """
        for element in tree.iter():
            for attrib_key, attrib_value in list(element.attrib.items()):
                if attrib_key in {"name", "ahbName"}:
                    element.attrib[attrib_key] = MigXmlReader.make_name_comparable(attrib_value)

    @abstractmethod
    def get_edifact_stack(
        self,
        segment_group_key: str,
        segment_key: str,
        data_element_id: str,
        name: str,
        #    previous_qualifier: Optional[str] = None,
    ) -> EdifactStack:
        """
        Returns the edifact stack for the given combination of segment group, key, data element and name
        """
        raise NotImplementedError("The inheriting class has to implement this method")


# pylint:disable=too-few-public-methods
@attr.s(auto_attribs=True, kw_only=True)
class _XQueryPathResult:
    """
    the (internal) result of a query path search inside the tree.
    """

    is_unique: Optional[bool]  #: True iff unique, None for no results, False for >1 result
    unique_result: Optional[Element]  #: unique element if there is any; None otherwise
    candidates: Optional[List[Element]]  #: list of candidates if there is >1 result


# pylint:disable=c-extension-no-member
class MigXmlReader(MigReader):
    """
    Reads an XML file an transforms it into a Segment Group Hierarchy
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
        # the original tree is the unmodified MIG XML Structure with all its quircks
        self._original_tree: etree.ElementTree = etree.ElementTree(self._original_root)
        # but turns out it's much easier to handle a sanitized tree that is simplified in a sense that
        # * has only lower case (ahb)names which are easy to match because they don't contain whitespace,"-" or casing
        # * has the same structure as the _original_tree so that absolute path expressions from the sanitized tree match
        self._sanitized_tree: etree.ElementTree = etree.ElementTree(self._sanitized_root)
        MigReader.make_tree_names_comparable(self._sanitized_tree)

    def get_format_name(self) -> str:
        """
        the root element of the XML is the name of the EDIFACT format
        """
        return self._original_root.tag

    def element_to_edifact_stack(self, element: etree.Element, use_sanitized_tree: bool) -> EdifactStack:
        """
        extract the edifact seed path from the given element
        :return:
        """
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
            if "ahbName" in leaf_element.attrib:
                level_name = leaf_element.attrib["ahbName"]
            else:
                level_name = leaf_element.attrib["name"]
            stack.levels.append(EdifactStackLevel(name=level_name, is_groupable=leaf_element.tag == "class"))
        return stack

    @staticmethod
    def _list_to_xquerypathresult(candidates: List[Element]) -> _XQueryPathResult:
        if len(candidates) == 0:
            return _XQueryPathResult(candidates=None, is_unique=None, unique_result=None)
            # the == 1 case is handled last
        if len(candidates) > 1:
            return _XQueryPathResult(candidates=candidates, is_unique=False, unique_result=None)
        return _XQueryPathResult(candidates=None, is_unique=True, unique_result=candidates[0])

    def get_unique_result_by_xpath(self, query_path: str, use_sanitized_tree: bool) -> _XQueryPathResult:
        """
        Tries to find an element for the given query path.
        If there's exactly 1 result, it is returned.
        If there are 0 or >1 results a ValueError is raised.
        """
        candidates: List[Element]
        if use_sanitized_tree:
            candidates = list(self._sanitized_root.xpath(query_path))
        else:
            candidates = list(self._original_root.xpath(query_path))
        return MigXmlReader._list_to_xquerypathresult(candidates)

    def get_unique_result_by_segment_group(
        self, candidates: List[Element], segment_group_key: str, use_sanitized_tree: bool
    ) -> _XQueryPathResult:
        """
        keep those elements that have the correct segment_group_key
        """
        filtered = [
            e
            for e in candidates
            if self.get_parent_segment_group_key(e, use_sanitized_tree=use_sanitized_tree) == segment_group_key
        ]
        return MigXmlReader._list_to_xquerypathresult(filtered)

    @staticmethod
    def _get_segment_group_key_or_none(element: Element) -> Optional[str]:
        """
        returns the segment group of element if present; None otherwise
        """
        if "ref" in element.attrib and element.attrib["ref"].startswith("SG"):
            # the trivial case
            return element.attrib["ref"]
        return None

    def get_parent_segment_group_key(self, element: Element, use_sanitized_tree: bool) -> Optional[str]:
        """
        iterate from element towards root and return the first segment group found (the one closes to element).
        returns None if no segment group was found
        """
        segment_group_key = MigXmlReader._get_segment_group_key_or_none(element)
        if segment_group_key is not None:
            return segment_group_key
        if use_sanitized_tree:
            xpath = self._sanitized_tree.getpath(element)
        else:
            xpath = self._original_tree.getpath(element)
        path_parts = list(xpath.split("/"))
        sub_paths: List[str] = []
        for depth in range(2, len(path_parts)):
            sub_path = "/".join(path_parts[0:depth])
            sub_paths.append(sub_path)
        # if xpath was "/foo/bar/asd/xyz", sub_paths is ["/foo", "/foo/bar", "/foo/bar/asd"] now (xyz is not contained!)
        sub_paths.reverse()
        for sub_path in sub_paths:
            leaf_element = self._original_root.xpath(sub_path)[0]  # type:ignore[attr-defined]
            segment_group_key = MigXmlReader._get_segment_group_key_or_none(leaf_element)
            if segment_group_key is not None:
                return segment_group_key
        return None

    # pylint:disable=unused-argument
    def get_edifact_stack(
        self,
        segment_group_key: str,
        segment_key: str,
        data_element_id: str,
        name: str,
        #       previous_qualifier: Optional[str] = None,
    ) -> EdifactStack:
        """
        get the edifact stack for the given segment_group, segment... combination
        :return:
        """
        segment_de_result = self.get_unique_result_by_xpath(
            f".//*[@meta.id='{data_element_id}' and starts-with(@ref, '{segment_key}')]", use_sanitized_tree=False
        )
        if segment_de_result.is_unique:
            return self.element_to_edifact_stack(segment_de_result.unique_result, use_sanitized_tree=False)
        if segment_de_result.is_unique is False and segment_de_result.candidates is not None:
            filtered_by_names = [
                x
                for x in segment_de_result.candidates
                if MigReader.are_similar_names(x.attrib["name"], name)
                or ("ahbName" in x.attrib and MigReader.are_similar_names(x.attrib["ahbName"], name))
            ]
            if len(filtered_by_names) == 0:
                # try to find by parents name
                via_parents_name_result = self.get_unique_result_by_xpath(
                    # pylint:disable=line-too-long
                    f".//class[@name='{MigReader.make_name_comparable(name)}']/*[@meta.id='{data_element_id}' and starts-with(@ref, '{segment_key}')]",
                    use_sanitized_tree=True,
                )
                if via_parents_name_result.is_unique:
                    return self.element_to_edifact_stack(via_parents_name_result.unique_result, use_sanitized_tree=True)
                if via_parents_name_result.candidates is None:
                    via_parents_ahb_name_result = self.get_unique_result_by_xpath(
                        # pylint:disable=line-too-long
                        f".//class[@ahbName='{MigReader.make_name_comparable(name)}']/*[@meta.id='{data_element_id}' and starts-with(@ref, '{segment_key}')]",
                        use_sanitized_tree=True,
                    )
                    if via_parents_ahb_name_result.is_unique:
                        return self.element_to_edifact_stack(
                            via_parents_ahb_name_result.unique_result, use_sanitized_tree=True
                        )
            elif len(filtered_by_names) == 1:
                return self.element_to_edifact_stack(filtered_by_names[0], use_sanitized_tree=False)
            else:  # len(filtered_by_names) >1
                filtered_by_sg = self.get_unique_result_by_segment_group(
                    filtered_by_names, segment_group_key, use_sanitized_tree=False
                )
                if filtered_by_sg.is_unique:
                    return self.element_to_edifact_stack(filtered_by_sg.unique_result, use_sanitized_tree=False)

        raise ValueError("No idea")

    def to_segment_group_hierarchy(self) -> SegmentGroupHierarchy:
        """
        convert the read data into a segment group hierarchy
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")
