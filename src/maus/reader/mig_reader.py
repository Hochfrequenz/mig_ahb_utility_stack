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
        if name_x.lower() == name_y.lower():  # type:ignore[union-attr]
            return True
        return False


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
        self.root: etree._Element
        if isinstance(init_param, str):
            self.root = etree.fromstring(init_param)
        elif isinstance(init_param, Path):
            self.root = etree.parse(str(init_param.absolute())).getroot()
        else:
            raise ValueError(f"The type of '{init_param}' is not valid")
        self.tree = etree.ElementTree(self.root)

    def get_format_name(self) -> str:
        """
        the root element of the XML is the name of the EDIFACT format
        """
        return self.root.tag

    def element_to_edifact_seed_path(self, element: etree._Element) -> str:
        """
        extract the edifact seed path from the given element
        :return:
        """
        xpath = self.tree.getpath(element)
        result_list: List[str] = []
        iter_path = "/" + xpath.split("/")[1]
        for leaf in xpath.split("/")[2:]:
            iter_path += "/" + leaf
            leaf_element = self.root.xpath(iter_path)[0]  # type:ignore[attr-defined]
            result_list.append(leaf_element.attrib["name"])
        return "->".join(result_list)

    def get_unique_result_by_xpath(self, query_path: str) -> _XQueryPathResult:
        """
        Tries to find an element for the given query path.
        If there's exactly 1 result, it is returned.
        If there are 0 or >1 results a ValueError is raised.
        """
        candidates = list(self.root.xpath(query_path))
        if len(candidates) == 0:
            return _XQueryPathResult(candidates=None, is_unique=None, unique_result=None)
            # the == 1 case is handled last
        if len(candidates) > 1:
            return _XQueryPathResult(candidates=candidates, is_unique=False, unique_result=None)
        return _XQueryPathResult(candidates=None, is_unique=True, unique_result=candidates[0])

    # pylint:disable=unused-argument
    def get_edifact_seed_path(
        self, segment_group_key: str, segment_key: str, data_element_id: str, name: Optional[str] = None
    ) -> str:
        """
        get the edifact seed path for the given segment_group, segment... combination
        :return:
        """
        segment_de_result = self.get_unique_result_by_xpath(
            f".//*[@meta.id='{data_element_id}' and starts-with(@ref, '{segment_key}')]"
        )
        if segment_de_result.is_unique:
            return self.element_to_edifact_seed_path(segment_de_result.unique_result)
        if segment_de_result.is_unique is False and segment_de_result.candidates is not None:
            filtered_by_names = [
                x for x in segment_de_result.candidates if MigReader.are_similar_names(x.attrib["name"], name)
            ]
            if len(filtered_by_names) == 0:
                # try to find by parents name
                via_parents_name_result = self.get_unique_result_by_xpath(
                    f".//class[@name='{name}']/*[@meta.id='{data_element_id}' and starts-with(@ref, '{segment_key}')]"
                )
                if via_parents_name_result.is_unique:
                    return self.element_to_edifact_seed_path(via_parents_name_result.unique_result)
        raise ValueError("No idea")

    def to_segment_group_hierarchy(self) -> SegmentGroupHierarchy:
        """
        convert the read data into a segment group hierarchy
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")
