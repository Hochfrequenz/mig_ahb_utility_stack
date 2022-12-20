"""
MAUS is the MIG AHB Utility stack.
This module contains methods to merge data from Message Implementation Guide and Anwendungshandbuch
"""
from itertools import groupby
from typing import List, Sequence

from more_itertools import first, last

from maus.models.anwendungshandbuch import AhbLine, DeepAnwendungshandbuch, FlatAnwendungshandbuch
from maus.models.edifact_components import (
    DataElement,
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    SegmentLevel,
    ValuePoolEntry,
    derive_data_type_from_segment_code,
)
from maus.models.message_implementation_guide import SegmentGroupHierarchy
from maus.navigation import AhbLocation, calculate_distance, determine_locations


def merge_lines_with_same_data_element(ahb_lines: Sequence[AhbLine]) -> DataElement:
    """
    Merges lines that have the same data element into a single data element instance which is returned
    """
    distinct_data_element_keys = {ahb_line.data_element for ahb_line in ahb_lines}
    if len(distinct_data_element_keys) != 1:
        raise ValueError(
            "You must only use this function with lines that share the same data element but the "
            f"parameter ahb_lines contains: {', '.join([x or '' for x in distinct_data_element_keys])} "
        )
    result: DataElement
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
        result = DataElementFreeText(
            entered_input=None,
            ahb_expression=ahb_lines[0].ahb_expression,
            discriminator=ahb_lines[0].name or ahb_lines[0].get_discriminator(include_name=True),
            data_element_id=first(
                ahb_lines, lambda line: line.data_element is not None
            ).data_element,  # type:ignore[arg-type]
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
        this_segment_lines: List[AhbLine] = list(segments)
        if not this_segment_lines[0].ahb_expression:
            # segments with an empty AHB expression shall not be included
            # https://github.com/Hochfrequenz/mig_ahb_utility_stack/issues/38
            continue
        segment = Segment(
            discriminator=segment_key,  # type:ignore[arg-type] # shall not be none after sanitizing
            data_elements=[],
            ahb_expression=this_segment_lines[0].ahb_expression,
            section_name=this_segment_lines[0].section_name,
            ahb_line_index=this_segment_lines[0].index,
        )
        for data_element_key, data_element_lines in groupby(this_segment_lines, key=lambda line: line.data_element):
            if data_element_key is None:
                continue
            data_element = merge_lines_with_same_data_element(list(data_element_lines))
            segment.data_elements.append(data_element)  # type:ignore[union-attr] # yes, it's not none
        result.append(segment)
    return result


def group_lines_by_segment_group(
    ahb_lines: List[AhbLine], segment_group_hierarchy: SegmentGroupHierarchy
) -> List[SegmentGroup]:
    """
    Group the lines by their segment group and arrange the segment groups in a flat/not deep list
    """
    result: List[SegmentGroup] = []
    for hierarchy_segment_group, _ in segment_group_hierarchy.flattened():  # flatten = ignore hierarchy, preserve order
        # here we assume, that the ahb_lines are easily groupable
        # (meaning, the ran through FlatAhb.sort_lines_by_segment_groups once)
        for segment_group_key, sg_group in groupby(ahb_lines, key=lambda line: line.segment_group_key):
            if hierarchy_segment_group == segment_group_key:
                this_sg = list(sg_group)
                sg_draft = SegmentGroup(
                    discriminator=segment_group_key,  # type:ignore[arg-type] # might be None now, will be replace later
                    ahb_expression=(this_sg[0].ahb_expression or "").strip() or None,
                    segments=group_lines_by_segment(this_sg),
                    segment_groups=[],
                    ahb_line_index=this_sg[0].index,
                )
                result.append(sg_draft)
    return result


def to_deep_ahb(
    flat_ahb: FlatAnwendungshandbuch, segment_group_hierarchy: SegmentGroupHierarchy
) -> DeepAnwendungshandbuch:
    """
    Converts a flat ahb into a nested ahb using the provided segment hierarchy
    """
    result = DeepAnwendungshandbuch(meta=flat_ahb.meta, lines=[])
    parent_group_lists: List[List[SegmentGroup]] = []
    for position, layer_group in groupby(
        determine_locations(segment_group_hierarchy, flat_ahb.lines), key=lambda line_and_position: line_and_position[1]
    ):
        data_element_lines = [x[0] for x in layer_group]  # index 1 is the position
        if not any((True for line in data_element_lines if line.segment_code is not None)):
            continue  # section heading only
        if any((True for line in data_element_lines if line.data_element is not None)):
            if not any((True for line in data_element_lines if line.ahb_expression is not None)):
                # if none of the items is marked with an ahb expression it's probably not required in this AHB
                continue
            data_element = merge_lines_with_same_data_element(data_element_lines)
            append_next_data_elements_here.append(data_element)
        else:
            first_line = first(data_element_lines)
            last_line = last(data_element_lines)
            if (
                first_line.segment_group_key == last(position.layers).segment_group_key
                and last(position.layers).opening_segment_code == last_line.segment_code
            ):
                # a new segment group has been opened
                segment_group = SegmentGroup(
                    discriminator=first_line.segment_group_key or "root",
                    # type:ignore[arg-type] # might be None now, will be replaced later
                    ahb_expression=(first_line.ahb_expression or "Dummy MUSS SG").strip() or None,
                    segments=[],
                    segment_groups=[],
                    ahb_line_index=first_line.index,
                )
                if "append_next_segments_here" in locals():
                    del append_next_segments_here
                append_next_segments_here = segment_group.segments
                if segment_group.discriminator == "root":
                    result.lines.append(segment_group)
                    append_next_sg_here = segment_group.segment_groups
                    parent_group_lists.append(result.lines)
                elif position.is_sub_location_of(previous_position):
                    append_next_sg_here.append(segment_group)
                    parent_group_lists.append(append_next_sg_here)
                    if "append_next_sg_here" in locals():
                        del append_next_sg_here
                    append_next_sg_here = segment_group.segment_groups
                else:
                    # todo: breakpoint here for sg.discriminator=="SG4" what if prvious location and this locaiton are neighbours                    append_here = last(parent_group_lists)
                    distance = calculate_distance(previous_position, position)
                    for i in range(0, distance.layers_up):
                        append_next_sg_here = parent_group_lists.pop()
                    for j in range(0, distance.layers_down - 1):
                        parent_group_lists.append(append_next_sg_here)
                        append_next_sg_here = last(append_next_sg_here).segment_groups
                    append_next_sg_here.append(segment_group)
                    parent_group_lists.append(append_next_sg_here)
                    if "append_next_sg_here" in locals():
                        del append_next_sg_here
                    append_next_sg_here = segment_group.segment_groups

                    # append_here.append(segment_group)
                    # append_next_sg_here.append(segment_group)
            assert last_line.data_element is None
            assert last_line.segment_code is not None
            # this assertion is because we assume that the lines always come like this:
            # Section Heading
            # SGx Foo      <-- a line with only the segment code but no actual content; this is where we're right now
            # SGx Foo 1234 <-- the first interesting line
            segment = Segment(
                discriminator=last_line.segment_code,
                data_elements=[],
                ahb_expression=first_line.ahb_expression or "Dummy Muss S",
                section_name=first_line.section_name,
                ahb_line_index=first_line.index,
            )
            if "append_next_data_elements_here" in locals():
                del append_next_data_elements_here
            append_next_data_elements_here = segment.data_elements
            append_next_segments_here.append(segment)
        previous_position = position
    return result
