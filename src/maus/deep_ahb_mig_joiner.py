"""
A module to mix/join information from the deep ahb and the MIG (beyond SGH)
"""
from typing import Optional

from maus import DataElementFreeText, DataElementValuePool, DeepAnwendungshandbuch
from maus.reader.mig_reader import MigReader


def replace_discriminators_with_edifact_stack(deep_ahb: DeepAnwendungshandbuch, mig_reader: MigReader) -> None:
    """
    replaces all discriminators in deep_ahb with an edifact seed path from the provided mig_reader
    """
    for segment_group_index, segment_group in enumerate(deep_ahb.lines):
        current_segment_group_key = segment_group.discriminator
        # todo: also loop over the segment groups inside the segment group
        for segment_index, segment in enumerate(segment_group.segments):  # type:ignore[union-attr]
            if mig_reader.is_edifact_boilerplate(segment.discriminator):
                continue
            current_segment_key = segment.discriminator
            predecessor_qualifier: Optional[str] = None
            for de_index, data_element in enumerate(segment.data_elements):
                if isinstance(data_element, DataElementFreeText):
                    deep_ahb.lines[segment_group_index].segments[segment_index].data_elements[
                        de_index
                    ].discriminator = mig_reader.get_edifact_stack(
                        segment_group_key=current_segment_group_key,
                        segment_key=current_segment_key,
                        data_element_id=data_element.data_element_id,
                        name=data_element.discriminator,
                        predecessor_qualifier=predecessor_qualifier,
                    ).to_json_path()
                if isinstance(data_element, DataElementValuePool):
                    edifact_stack = mig_reader.get_edifact_stack(
                        segment_group_key=current_segment_group_key,
                        segment_key=current_segment_key,
                        data_element_id=data_element.data_element_id,
                        name=data_element.discriminator,
                        predecessor_qualifier=predecessor_qualifier,
                    )
                    if edifact_stack is not None:
                        deep_ahb.lines[segment_group_index].segments[segment_index].data_elements[
                            de_index
                        ].discriminator = edifact_stack.to_json_path()
                    if len(data_element.value_pool) == 1:
                        predecessor_qualifier = list(data_element.value_pool.keys())[0]
                    else:
                        predecessor_qualifier = None
