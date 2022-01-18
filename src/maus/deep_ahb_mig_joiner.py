"""
A module to mix/join information from the deep ahb and the MIG (beyond SGH)
"""
from typing import List, Optional

from maus import DataElementFreeText, DataElementValuePool, DeepAnwendungshandbuch
from maus.models.edifact_components import EdifactStackQuery, Segment, SegmentGroup
from maus.reader.mig_reader import MigReader


def _replace_disciminators_with_edifact_stack_segments(
    segments: List[Segment], segment_group_key: str, mig_reader: MigReader
) -> List[Segment]:
    result = segments.copy()
    for segment_index, segment in enumerate(segments):  # type:ignore[union-attr]
        if mig_reader.is_edifact_boilerplate(segment.discriminator):
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
                )
                stack = mig_reader.get_edifact_stack(query)
                # for easy error analysis set a conditional break point here for 'stack is None'
                if stack is not None:
                    result[segment_index].data_elements[de_index].discriminator = stack.to_json_path()
                else:
                    raise ValueError(f"Couldn't find a stack for {query}")
            if isinstance(data_element, DataElementValuePool):
                edifact_stack = mig_reader.get_edifact_stack(
                    EdifactStackQuery(
                        segment_group_key=segment_group_key,
                        segment_code=current_segment_key,
                        data_element_id=data_element.data_element_id,
                        name=None,
                        predecessor_qualifier=predecessor_qualifier,
                    )
                )
                if edifact_stack is not None:
                    result[segment_index].data_elements[de_index].discriminator = edifact_stack.to_json_path()
                if len(data_element.value_pool) == 1:
                    predecessor_qualifier = list(data_element.value_pool.keys())[0]
                else:
                    predecessor_qualifier = None
    return result


def _replace_discriminators_with_edifact_stack_groups(
    segment_groups: List[SegmentGroup], mig_reader: MigReader
) -> List[SegmentGroup]:
    """
    replaces all discriminators in the given list of segment groups with an edifact seed path from the provided reader
    """
    result = segment_groups.copy()
    for segment_group_index, segment_group in enumerate(segment_groups):
        current_segment_group_key = segment_group.discriminator
        if result[segment_group_index].segments is not None:
            result[segment_group_index].segments = _replace_disciminators_with_edifact_stack_segments(
                segments=result[segment_group_index].segments,  # type:ignore[arg-type]
                segment_group_key=current_segment_group_key,
                mig_reader=mig_reader,
            )
        if result[segment_group_index].segment_groups is not None:
            result[segment_group_index].segment_groups = _replace_discriminators_with_edifact_stack_groups(
                segment_groups=segment_group.segment_groups,  # type:ignore[arg-type]
                mig_reader=mig_reader,
            )
    return result


def replace_discriminators_with_edifact_stack(deep_ahb: DeepAnwendungshandbuch, mig_reader: MigReader) -> None:
    """
    replaces all discriminators in deep_ahb with an edifact seed path from the provided mig_reader
    """
    deep_ahb.lines = _replace_discriminators_with_edifact_stack_groups(deep_ahb.lines, mig_reader)
