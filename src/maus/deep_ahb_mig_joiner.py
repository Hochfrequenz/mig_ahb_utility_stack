"""
A module to mix/join information from the deep ahb and the MIG (beyond SGH)
"""
from typing import Dict, List, Optional, Set, Tuple

from maus import DataElementFreeText, DataElementValuePool, DeepAnwendungshandbuch
from maus.edifact import is_edifact_boilerplate
from maus.models.edifact_components import EdifactStackQuery, Segment, SegmentGroup
from maus.reader.mig_reader import MigReader


def _replace_disciminators_with_edifact_stack_segments(
    segments: List[Segment],
    segment_group_key: str,
    mig_reader: MigReader,
    # the fallback_predecessors are kind of a "overflow" / "Übertrag" from parent segment groups
    # without the fallback_predecessors the single segment groups would be handled independently of each other,
    # which is great for readability, debuggability and testing
    # but sadly the complexity of the AHBs requires a coupling.
    fallback_predecessors: Dict[str, Set[str]],
    ignore_errors: bool = False,
) -> Tuple[List[Segment], Dict[str, Set[str]]]:
    result = segments.copy()
    predecessors_used: Dict[str, Set[str]] = {}  # maps the segment code to a set of qualifiers used as predecessors
    for segment_index, segment in enumerate(segments):  # type:ignore[union-attr]
        if is_edifact_boilerplate(segment.discriminator):
            continue
        current_segment_key = segment.discriminator
        predecessor_qualifier: Optional[str] = None
        for de_index, data_element in enumerate(segment.data_elements):
            if isinstance(data_element, DataElementFreeText):
                query = EdifactStackQuery(
                    segment_group_key=segment_group_key,
                    segment_code=current_segment_key,
                    data_element_id=data_element.data_element_id,
                    name=data_element.discriminator,
                    predecessor_qualifier=predecessor_qualifier,
                    section_name=segment.section_name,
                )
                stack = mig_reader.get_edifact_stack(query)
                # for easy error analysis set a conditional break point here for 'stack is None'
                if stack is not None:
                    result[segment_index].data_elements[de_index].discriminator = stack.to_json_path()
                else:
                    if not ignore_errors:
                        raise ValueError(f"Couldn't find a stack for {query}")
            if isinstance(data_element, DataElementValuePool):
                query = EdifactStackQuery(
                    segment_group_key=segment_group_key,
                    segment_code=current_segment_key,
                    data_element_id=data_element.data_element_id,
                    name=None,
                    predecessor_qualifier=predecessor_qualifier,
                    section_name=segment.section_name,
                )
                edifact_stack = mig_reader.get_edifact_stack(query)
                if edifact_stack is not None:
                    result[segment_index].data_elements[de_index].discriminator = edifact_stack.to_json_path()
                if edifact_stack is None and len(data_element.value_pool) > 1:
                    if predecessor_qualifier is None:
                        all_fallback_predecessors: List[str] = []
                        for predecessor_set in fallback_predecessors.values():
                            for value in predecessor_set:
                                all_fallback_predecessors.append(value)
                        for fallback_predecessor in all_fallback_predecessors:
                            query = EdifactStackQuery(
                                segment_group_key=segment_group_key,
                                segment_code=current_segment_key,
                                data_element_id=data_element.data_element_id,
                                name=None,
                                predecessor_qualifier=fallback_predecessor,
                                section_name=segment.section_name,
                            )
                            edifact_stack = mig_reader.get_edifact_stack(query)
                            if edifact_stack is not None:
                                result[segment_index].data_elements[
                                    de_index
                                ].discriminator = edifact_stack.to_json_path()
                                break
                    if edifact_stack is None and not ignore_errors:
                        raise ValueError(f"Any value pool with more than 1 entry has to have an edifact stack {query}")
                if len(data_element.value_pool) == 1:
                    predecessor_qualifier = data_element.value_pool[0].qualifier
                    try:
                        predecessors_used[current_segment_key].add(predecessor_qualifier)
                    except KeyError:
                        predecessors_used[current_segment_key] = {predecessor_qualifier}
                else:
                    predecessor_qualifier = None
    return result, predecessors_used


def _replace_discriminators_with_edifact_stack_groups(
    segment_groups: List[SegmentGroup],
    mig_reader: MigReader,
    fallback_predecessors: Dict[str, Set[str]],
    ignore_errors: bool = False,
) -> List[SegmentGroup]:
    """
    replaces all discriminators in the given list of segment groups with an edifact seed path from the provided reader
    """
    result = segment_groups.copy()
    for segment_group_index, segment_group in enumerate(segment_groups):
        current_segment_group_key = segment_group.discriminator
        if result[segment_group_index].segments is not None:
            segments_result, predecessor_qualifiers_used = _replace_disciminators_with_edifact_stack_segments(
                segments=result[segment_group_index].segments,  # type:ignore[arg-type]
                segment_group_key=current_segment_group_key,
                mig_reader=mig_reader,
                ignore_errors=ignore_errors,
                fallback_predecessors=fallback_predecessors,
            )
            result[segment_group_index].segments = segments_result
        if result[segment_group_index].segment_groups is not None:
            result[segment_group_index].segment_groups = _replace_discriminators_with_edifact_stack_groups(
                segment_groups=segment_group.segment_groups,  # type:ignore[arg-type]
                mig_reader=mig_reader,
                ignore_errors=ignore_errors,
                fallback_predecessors=predecessor_qualifiers_used,
            )
    return result


def replace_discriminators_with_edifact_stack(
    deep_ahb: DeepAnwendungshandbuch, mig_reader: MigReader, ignore_errors: bool = False
) -> None:
    """
    replaces all discriminators in deep_ahb with an edifact seed path from the provided mig_reader
    """
    deep_ahb.lines = _replace_discriminators_with_edifact_stack_groups(deep_ahb.lines, mig_reader, ignore_errors)
