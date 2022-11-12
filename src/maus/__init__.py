"""
MAUS is the MIG AHB Utility stack.
This module contains methods to merge data from Message Implementation Guide and Anwendungshandbuch
"""
from itertools import groupby
from typing import List, Optional, Sequence

from more_itertools import first_true, split_when  # type:ignore[import]

from maus.models.anwendungshandbuch import AhbLine, DeepAnwendungshandbuch, FlatAnwendungshandbuch
from maus.models.edifact_components import (
    DataElement,
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
    derive_data_type_from_segment_code,
)
from maus.models.message_implementation_guide import SegmentGroupHierarchy


def merge_lines_with_same_data_element(ahb_lines: Sequence[AhbLine]) -> Optional[DataElement]:
    """
    Merges lines that have the same data element into a single data element instance which is returned
    """
    distinct_data_element_keys = {ahb_line.data_element for ahb_line in ahb_lines}
    if len(distinct_data_element_keys) != 1:
        raise ValueError(
            "You must only use this function with lines that share the same data element but the "
            f"parameter ahb_lines contains: {', '.join([x or '' for x in distinct_data_element_keys])} "
        )
    result: Optional[DataElement] = None
    if ahb_lines[0].value_pool_entry is not None:
        result = DataElementValuePool(
            discriminator=ahb_lines[0].get_discriminator(include_name=False),
            value_pool=[],
            data_element_id=ahb_lines[0].data_element,  # type:ignore[arg-type]
            entered_input=None,
        )
        for data_element_value_entry in ahb_lines:
            if data_element_value_entry.name is None:
                # pylint:disable=fixme
                # todo: this is line where there is only a description and nothing else. i hate it
                # e.g. there is 35001: https://github.com/Hochfrequenz/mig_ahb_utility_stack/issues/21
                continue
            if not data_element_value_entry.ahb_expression:
                # value pool entries with empty/None AHB expression shall not be included
                # https://github.com/Hochfrequenz/mig_ahb_utility_stack/issues/38
                continue
            value_pool_entry = ValuePoolEntry(
                qualifier=data_element_value_entry.value_pool_entry,  # type:ignore[arg-type]
                meaning=data_element_value_entry.name.strip(),  # type:ignore[assignment,union-attr]
                ahb_expression=data_element_value_entry.ahb_expression,
            )
            result.value_pool.append(value_pool_entry)  # type:ignore[index]
    else:
        ahb_expression = (ahb_lines[0].ahb_expression or "").strip() or None
        if ahb_expression is not None:
            result = DataElementFreeText(
                entered_input=None,
                ahb_expression=ahb_expression,
                discriminator=ahb_lines[0].name or ahb_lines[0].get_discriminator(include_name=True),
                data_element_id=ahb_lines[0].data_element,  # type:ignore[arg-type]
            )
            # a free text field never spans more than 1 line
            data_type = derive_data_type_from_segment_code(ahb_lines[0].segment_code)  # type:ignore[arg-type]
            if data_type is not None:
                result.value_type = data_type
    return result


def group_lines_by_segment(segment_group_lines: List[AhbLine]) -> List[Segment]:
    """
    convert the given lines (which are assumed to be from the same segment group) into single segments
    """
    result: List[Segment] = []
    for segment_key, segments in groupby(segment_group_lines, key=lambda line: line.segment_code):
        if segment_key is None:
            continue  # filter out segment group level
        this_segment_lines = list(segments)
        if not this_segment_lines[0].ahb_expression:
            # segments with an empty AHB expression shall not be included
            # https://github.com/Hochfrequenz/mig_ahb_utility_stack/issues/38
            continue
        segment = Segment(
            discriminator=segment_key,  # type:ignore[arg-type] # shall not be none after sanitizing
            data_elements=[],
            ahb_expression=this_segment_lines[0].ahb_expression,
            section_name=this_segment_lines[0].section_name,
        )
        for data_element_key, data_element_lines in groupby(this_segment_lines, key=lambda line: line.data_element):
            if data_element_key is None:
                continue
            data_element = merge_lines_with_same_data_element(list(data_element_lines))
            if data_element is not None:
                segment.data_elements.append(data_element)  # type:ignore[union-attr] # yes, it's not none
        result.append(segment)
    return result


def _is_opening_segment_line_border(this_line: AhbLine, next_line: AhbLine, opening_segment_code: str) -> bool:
    """
    returns true iff this_line and next_line are the border between two neighboughring segment groups with the same
    segment group key
    :param this_line:
    :param next_line:
    :param opening_segment_code:
    :return:
    """
    this_line_is_opening_segment = this_line.segment_code == opening_segment_code
    next_line_is_opening_segment = this_line.segment_code != opening_segment_code and next_line == opening_segment_code
    next_line_has_empty_segment = next_line.segment_code is None
    if next_line_is_opening_segment is False and next_line_has_empty_segment is False:
        return False
    return (not this_line_is_opening_segment) and next_line_has_empty_segment


def group_lines_by_segment_group(
    ahb_lines: List[AhbLine], segment_group_hierarchy: SegmentGroupHierarchy
) -> List[SegmentGroup]:
    """
    Group the lines by their segment group and arrange the segment groups in a flat/not deep list
    """
    result: List[SegmentGroup] = []
    # flatten = ignore hierarchy, preserve order
    for hierarchy_segment_group, opening_segment_code in segment_group_hierarchy.flattened():
        # here we assume, that the ahb_lines are easily groupable
        # (meaning, the ran through FlatAhb.sort_lines_by_segment_groups once)
        for segment_group_key, sg_group in groupby(ahb_lines, key=lambda line: line.segment_group_key):
            # There might be multiple segment groups with the same segment_group_key next to each other (SG12 addresses)
            # That's why it is not sufficient to only group by segment_group_key.
            # The bug symptom is, that if the first segment group with a key is not present in an AHB (like for example
            # the "SG12: Kunde des Lieferanten" is not necessary in 11042 but occurs first in the 11042 AHB with an
            # empty ahb expression, because it is required in the 11043, in the next column in the AHB), all segment
            # groups with the same key are removed from the DeepAnwendungshandbuch and the second SG12 has no chance to
            # stay in the deep ahb, although it's a distinct segment group, that just shares the same key.
            # To prevent this behaviour, we have to interrupt the groupby with a split_when everytime, that the segment
            # groups' opening segment occurs in the ahb_lines.
            if hierarchy_segment_group != segment_group_key:
                continue
            segment_groups_with_same_key: List[List[AhbLine]]
            if opening_segment_code is None:
                # there is only one root
                segment_groups_with_same_key = [sg_group]
            else:
                segment_groups_with_same_key = list(
                    split_when(sg_group, lambda x, y: _is_opening_segment_line_border(x, y, opening_segment_code))
                )
            for distinct_segment_group in segment_groups_with_same_key:
                this_sg = list(distinct_segment_group)
                try:
                    ahb_expression = first_true(
                        this_sg, pred=lambda line: ((line.ahb_expression or "").strip() or None) is not None
                    ).ahb_expression
                except AttributeError:
                    # This happens when none of the lines in the entire distinct_segment_group has an ahb_expression.
                    # It means that the group is indeed not necessary. One example are e.g. the first two SG12 in 11042
                    # AHB: "Kunde des Lieferanten" and "Korrespondenzanschrift des Kunden des Lieferanten" which are
                    # both only relevant in neighbouring 11043). So the SG12 is just an artefact of the paper and table
                    # based description.
                    continue
                if ahb_expression is not None:
                    sg_draft = SegmentGroup(
                        discriminator=segment_group_key,  # type:ignore[arg-type] # might be None, will replace later
                        ahb_expression=ahb_expression,
                        segments=group_lines_by_segment(this_sg),
                        segment_groups=[],
                    )
                    result.append(sg_draft)
    return result


def nest_segment_groups_into_each_other(
    flat_groups: List[SegmentGroup], segment_group_hierarchy: SegmentGroupHierarchy
) -> List[SegmentGroup]:
    """
    Take the pre-grouped but flat/"not nested" groups and nest them into each other as described in the SGH
    """
    result: List[SegmentGroup] = []
    for n, segment_group in enumerate(flat_groups):  # pylint:disable=invalid-name
        if segment_group.discriminator == segment_group_hierarchy.segment_group:
            # this is the root level for the given hierarchy
            result.append(segment_group)
            if segment_group_hierarchy.sub_hierarchy is None:
                break
            for sub_sgh in segment_group_hierarchy.sub_hierarchy:
                # pass the remaining groups to the remaining hierarchy
                sub_results = nest_segment_groups_into_each_other(flat_groups[n + 1 :], sub_sgh)
                for sub_result in sub_results:
                    # for any entry coming from nest_segment_groups_into_each other, it is ensured,
                    # that the segment groups are maybe an empty list but never None.
                    result[-1].segment_groups.append(sub_result)  # type:ignore[union-attr]
    return result


def to_deep_ahb(
    flat_ahb: FlatAnwendungshandbuch, segment_group_hierarchy: SegmentGroupHierarchy
) -> DeepAnwendungshandbuch:
    """
    Converts a flat ahb into a nested ahb using the provided segment hierarchy
    """
    result = DeepAnwendungshandbuch(meta=flat_ahb.meta, lines=[])
    flat_ahb.sort_lines_by_segment_groups()
    flat_groups = group_lines_by_segment_group(flat_ahb.lines, segment_group_hierarchy)
    # in a first step we group the lines by their segment groups but ignore the actual hierarchy except for the order
    result.lines = nest_segment_groups_into_each_other(flat_groups, segment_group_hierarchy)
    for segment_group in result.lines:
        if not isinstance(segment_group, SegmentGroup):
            continue
        if segment_group.discriminator is None:
            segment_group.discriminator = "root"
    return result
