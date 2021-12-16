"""
Classes that allow to read XML files that contain structural information (Message Implementation Guide information)
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union
from xml.etree.ElementTree import Element

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


# pylint:disable=c-extension-no-member
class MigXmlReader(MigReader):
    """
    Reads an XML file an transforms it into a Segment Group Hierarchy
    """

    def __init__(self, init_param: Union[str, Path]):
        self.root: Element
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

    def absolute_xpath_to_edifact_seed_path(self, xpath: str) -> str:
        """
        extract the edifact seed path from the given xpath
        :param xpath: absolute xpath (no filters, just key and indexes)
        :return:
        """
        result_list: List[str] = []
        iter_path = "/" + xpath.split("/")[1]
        for leaf in xpath.split("/")[2:]:
            iter_path += "/" + leaf
            leaf_element = self.root.xpath(iter_path)[0]  # type:ignore[attr-defined]
            result_list.append(leaf_element.attrib["name"])
        return "->".join(result_list)

    # pylint:disable=unused-argument
    def get_edifact_seed_path(
        self, segment_group_key: str, segment_key: str, data_element_id: str, name: Optional[str] = None
    ) -> str:
        """
        get the edifact seed path for the given segment_group, segment... combination
        :return:
        """
        xpath = f".//*[@meta.id='{data_element_id}' and starts-with(@ref, '{segment_key}')]"
        candidates = list(self.root.xpath(xpath))  # type:ignore[attr-defined]
        if len(candidates) == 0:
            raise ValueError(f"There's no match for ''{xpath}''")
        if len(candidates) == 1:
            return candidates[0]
        if name:
            filtered_by_names = [x for x in candidates if MigReader.are_similar_names(x.attrib["name"], name)]
            if len(filtered_by_names) > 1:
                raise ValueError(f"There are multiple results for '{name}'")
            if len(filtered_by_names) == 0:
                raise ValueError(f"There is no match for name '{name}'")
            absolute_path = self.tree.getpath(filtered_by_names[0])
            return self.absolute_xpath_to_edifact_seed_path(absolute_path)
        raise ValueError("No idea")

    def to_segment_group_hierarchy(self) -> SegmentGroupHierarchy:
        """
        convert the read data into a segment group hierarchy
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")
