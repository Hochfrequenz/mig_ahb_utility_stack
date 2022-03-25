"""
Classes that allow to read XML files that contain structural information (Message Implementation Guide information)
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Literal, Optional, TypeVar, Union
from xml.etree.ElementTree import Element

from lxml import etree  # type:ignore[import]

from maus import SegmentGroupHierarchy
from maus.models._internal import EdifactStackSearchStrategy, MigFilterResult
from maus.models.edifact_components import EdifactStack, EdifactStackLevel, EdifactStackQuery
from maus.reader.etree_element_helpers import (
    filter_by_name,
    filter_by_section_name,
    get_nested_qualifier,
    get_segment_group_key_or_none,
    list_to_mig_filter_result,
)
from maus.reader.mig_ahb_name_helpers import make_name_comparable, make_tree_names_comparable


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

    # pylint:disable=too-many-arguments
    @abstractmethod
    def get_edifact_stack(self, query: EdifactStackQuery) -> Optional[EdifactStack]:
        """
        Returns the edifact stack for the given combination of segment group, key, data element and name
        """
        raise NotImplementedError("The inheriting class has to implement this method")


Result = TypeVar("Result")  #: is a type var to indicate an "arbitrary but same" type in a generic function


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
        make_tree_names_comparable(self._sanitized_tree)

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
            if "ahbName" in leaf_element.attrib:
                level_name = leaf_element.attrib["ahbName"]
            else:
                level_name = leaf_element.attrib["name"]
            # https://stackoverflow.com/questions/47972143/using-attr-with-pylint
            # pylint: disable=no-member
            stack.levels.append(EdifactStackLevel(name=level_name, is_groupable=leaf_element.tag == "class"))
        return stack

    @staticmethod
    def get_unique_result_by_name(candidates: List[Element], query: EdifactStackQuery) -> MigFilterResult:
        """
        returns those elements that have the given name
        """
        # this method is directly unittests. Please refer to the test for some easy to debug examples.
        filtered_by_names = filter_by_name(candidates, query)
        return list_to_mig_filter_result(filtered_by_names)

    @staticmethod
    def get_unique_result_by_section_name(candidates: List[Element], query: EdifactStackQuery) -> MigFilterResult:
        """
        keeps those elements from the candidates whose where the name matches the query section name.
        Does _not_ create a new xpath.
        """
        # this method is directly unittests. Please refer to the test for some easy to debug examples.
        filtered_by_names = filter_by_section_name(candidates, query)
        return list_to_mig_filter_result(filtered_by_names)

    def get_unique_result_by_xpath(self, query_path: str, use_sanitized_tree: bool) -> MigFilterResult:
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
        return list_to_mig_filter_result(candidates)

    def get_unique_result_by_segment_group(
        self, candidates: List[Element], query: EdifactStackQuery, use_sanitized_tree: bool
    ) -> MigFilterResult:
        """
        keep those elements that have the correct segment_group_key
        """
        # this method is separately unittests; see the tests to get an understanding of the way it works.
        filtered = [
            e
            for e in candidates
            if self.get_parent_segment_group_key(e, use_sanitized_tree=use_sanitized_tree) == query.segment_group_key
        ]
        return list_to_mig_filter_result(filtered)

    # pylint:disable=no-self-use
    def get_unique_result_by_predecessor(self, candidates: List[Element], query: EdifactStackQuery) -> MigFilterResult:
        """
        Keep those elements that have (in the field) the given predecessor qualifier
        """
        # this method is separately unittests; see the tests to get an understanding of the way it works.
        relevant_attribute: Literal["key", "ref"]
        if query.segment_code == "RFF":
            relevant_attribute = "key"
        else:
            relevant_attribute = "ref"
        filtered_by_predecessor = [
            c for c in candidates if get_nested_qualifier(relevant_attribute, c) == query.predecessor_qualifier
        ]  # that's a bit dirty, better parse the ref properly instead of string-matching
        return list_to_mig_filter_result(filtered_by_predecessor)

    def get_unique_result_by_parent_predecessor(
        self, candidates: List[Element], query: EdifactStackQuery
    ) -> MigFilterResult:
        """
        Keep those elements that have (in the parent class) the given predecessor qualifier
        """
        # this method is separately unittests; see the tests to get an understanding of the way it works.
        filtered_by_predecessor = [
            c
            for c in candidates
            if self.get_parent_predecessor(c, use_sanitized_tree=False) == query.predecessor_qualifier
        ]
        return list_to_mig_filter_result(filtered_by_predecessor)

    def get_unique_result_by_parent_segment_group(
        self, candidates: List[Element], query: EdifactStackQuery
    ) -> MigFilterResult:
        """
        Keep those elements that have (in the parent class) the given segment group key
        """
        filtered_by_segment_group_key = [
            c
            for c in candidates
            if self.get_parent_segment_group_key(c, use_sanitized_tree=False) == query.segment_group_key
        ]
        return list_to_mig_filter_result(filtered_by_segment_group_key)

    def _get_parent_x(
        self, element: Element, evaluator: Callable[[Element], Result], use_sanitized_tree: bool
    ) -> Optional[Result]:
        """
        get the 'X' property of the parent where 'X' is the result of the evaluator when applied to an element.
        returns None if not found
        """
        result = evaluator(element)
        if result is not None:
            return result
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
        for sub_path in sub_paths:  # loop from inner to root
            leaf_element = self._original_root.xpath(sub_path)[0]  # type:ignore[attr-defined]
            result = evaluator(leaf_element)
            if result is not None:
                return result
        return None

    def get_parent_segment_group_key(self, element: Element, use_sanitized_tree: bool) -> Optional[str]:
        """
        iterate from element towards root and return the first segment group found (the one closes to element).
        returns None if no segment group was found
        """
        # This method is separately unit tested.
        # Reading the test will most likely make its behaviour more understandable.
        return self._get_parent_x(element, get_segment_group_key_or_none, use_sanitized_tree=use_sanitized_tree)

    def get_parent_predecessor(self, element: Element, use_sanitized_tree: bool) -> Optional[str]:
        """
        iterate from element towards root and return the first segment group found (the one closes to element).
        returns None if no segment group was found
        """
        # This method is separately unit tested.
        # Reading the test will most likely make its behaviour more understandable.
        return self._get_parent_x(
            element, lambda c: get_nested_qualifier("key", c), use_sanitized_tree=use_sanitized_tree
        )

    def _handle_predecessor_if_present(self, query: EdifactStackQuery) -> Optional[EdifactStackSearchStrategy]:
        """
        return a strategy for the predecessor if it's present in the query
        """
        if not query.predecessor_qualifier:
            return None
        return EdifactStackSearchStrategy(
            name="I filter by predecessor",
            filter=lambda q, c: self.get_unique_result_by_predecessor(
                c, q  # type:ignore[arg-type]
            ),
            unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                unique_result, use_sanitized_tree=False
            ),
            no_result_strategy=EdifactStackSearchStrategy(
                name="J filter by parent predecessor after predecessor lead to no result",
                filter=lambda q, c: self.get_unique_result_by_parent_predecessor(
                    c, q  # type:ignore[arg-type]
                ),
                no_result_strategy=EdifactStackSearchStrategy(
                    name="M filter by section_name==field name",
                    filter=lambda q, c: MigXmlReader.get_unique_result_by_section_name(c, q),  # type:ignore[arg-type]
                    unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                        unique_result, use_sanitized_tree=False
                    ),
                    no_result_strategy=None,
                    multiple_results_strategy=None,
                ),
                unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                    unique_result, use_sanitized_tree=False
                ),
                multiple_results_strategy=EdifactStackSearchStrategy(
                    name="K filter by parents segment group",
                    filter=lambda q, c: self.get_unique_result_by_parent_segment_group(
                        c, q  # type:ignore[arg-type]
                    ),
                    no_result_strategy=None,  # filter by its own predecessor :-(
                    unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                        unique_result, use_sanitized_tree=False
                    ),
                    multiple_results_strategy=None,
                ),  # Z18 goes here
            ),
            multiple_results_strategy=EdifactStackSearchStrategy(
                # doe snot work yet
                name="L filter by parents segment group because parent predecessor is not unique",
                filter=lambda q, c: self.get_unique_result_by_parent_segment_group(c, q),  # type:ignore[arg-type]
                unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                    unique_result, use_sanitized_tree=False
                ),
                multiple_results_strategy=None,
                no_result_strategy=None,
            ),
        )

    def _multiple_data_element_matches_handling(self, query: EdifactStackQuery) -> Optional[EdifactStackSearchStrategy]:
        if query.name is not None:
            return EdifactStackSearchStrategy(
                name="A filter by element name and ahb name",
                filter=lambda q, c: self.get_unique_result_by_name(c, q),  # type:ignore[arg-type]
                unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                    unique_result, use_sanitized_tree=False
                ),
                no_result_strategy=EdifactStackSearchStrategy(
                    name="B filter by parents name because direct name lead to no result",
                    filter=lambda q, _: self.get_unique_result_by_xpath(
                        # pylint:disable=line-too-long
                        f".//class[@name='{make_name_comparable(query.name)}']/*[@meta.id='{query.data_element_id}' and starts-with(@ref, '{query.segment_code}')]",  # type:ignore[arg-type]
                        use_sanitized_tree=True,
                    ),
                    unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                        unique_result, use_sanitized_tree=True
                    ),
                    no_result_strategy=EdifactStackSearchStrategy(
                        name="C filter by parents ahb name",
                        filter=lambda q, _: self.get_unique_result_by_xpath(
                            # pylint:disable=line-too-long
                            f".//class[@ahbName='{make_name_comparable(query.name)}']/*[@meta.id='{query.data_element_id}' and starts-with(@ref, '{query.segment_code}')]",  # type:ignore[arg-type]
                            use_sanitized_tree=True,
                        ),
                        unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                            unique_result, use_sanitized_tree=True
                        ),
                        multiple_results_strategy=None,
                        no_result_strategy=self._handle_predecessor_if_present(query),
                    ),
                    multiple_results_strategy=None,
                ),
                multiple_results_strategy=EdifactStackSearchStrategy(
                    name="D filter by segment group",
                    filter=lambda q, c: self.get_unique_result_by_segment_group(
                        c, q, use_sanitized_tree=False  # type:ignore[arg-type]
                    ),
                    unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                        unique_result, use_sanitized_tree=False
                    ),
                    multiple_results_strategy=EdifactStackSearchStrategy(
                        name="E filter by predecessor after segment group filter was not unique",
                        filter=lambda q, c: self.get_unique_result_by_predecessor(
                            c, q  # type:ignore[arg-type]
                        ),
                        unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                            unique_result, use_sanitized_tree=False
                        ),
                        multiple_results_strategy=None,  # raise ValueError("Predecessor B"),
                        no_result_strategy=EdifactStackSearchStrategy(
                            name="F filter by parent predecessor after predecessor lead to no result",
                            filter=lambda q, c: self.get_unique_result_by_parent_predecessor(
                                c, q  # type:ignore[arg-type]
                            ),
                            no_result_strategy=None,
                            multiple_results_strategy=None,
                            unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                                unique_result, use_sanitized_tree=False
                            ),
                        ),
                    ),
                    no_result_strategy=None,
                ),
            )
        if query.name is None and query.predecessor_qualifier is not None:
            return EdifactStackSearchStrategy(
                name="G filter by parent predecessor (no fallback)",
                filter=lambda q, c: self.get_unique_result_by_parent_predecessor(
                    c, q  # type:ignore[arg-type]
                ),
                unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                    unique_result, use_sanitized_tree=False
                ),
                no_result_strategy=EdifactStackSearchStrategy(
                    name="H filter by predecessor after parent predecessor lead to no result",
                    filter=lambda q, c: self.get_unique_result_by_predecessor(
                        c, q  # type:ignore[arg-type]
                    ),
                    unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                        unique_result, use_sanitized_tree=False
                    ),
                    multiple_results_strategy=None,
                    no_result_strategy=None,
                ),
                multiple_results_strategy=None,
            )
        return None

    def get_edifact_stack(self, query: EdifactStackQuery) -> Optional[EdifactStack]:
        """
        get the edifact stack for the given segment_group, segment... combination or None if there is no match
        """
        strategy = EdifactStackSearchStrategy(
            name="filter by data element id",
            filter=lambda q, _: (
                self.get_unique_result_by_xpath(
                    f".//*[@meta.id='{q.data_element_id}' and starts-with(@ref, '{q.segment_code}')]",
                    use_sanitized_tree=False,
                )
            ),
            unique_result_strategy=lambda unique_result: self.element_to_edifact_stack(
                unique_result, use_sanitized_tree=False
            ),
            no_result_strategy=None,  # if there is no matching data element, there's no chance to find a stack
            multiple_results_strategy=self._multiple_data_element_matches_handling(query),
        )
        return strategy.apply(query)

    def to_segment_group_hierarchy(self) -> SegmentGroupHierarchy:
        """
        convert the read data into a segment group hierarchy
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")
