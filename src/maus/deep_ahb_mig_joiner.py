"""
A module to mix/join information from the deep ahb and the MIG (beyond SGH)
"""
from maus import DataElementFreeText, DeepAnwendungshandbuch
from maus.reader.mig_reader import MigReader


def replace_discriminators_with_edifact_stack(deep_ahb: DeepAnwendungshandbuch, mig_reader: MigReader) -> None:
    """
    replaces all discriminators in deep_ahb with an edifact seed path from the provided mig_reader
    """
    for segment_group in deep_ahb.lines:
        current_segment_group_key = segment_group.discriminator
        for segment in segment_group.segments:  # type:ignore[union-attr]
            current_segment_key = segment.discriminator
            for data_element in segment.data_elements:
                if isinstance(data_element, DataElementFreeText):
                    data_element.discriminator = mig_reader.get_edifact_stack(
                        segment_group_key=current_segment_group_key,
                        segment_key=current_segment_key,
                        data_element_id=data_element.data_element_id,
                        name=data_element.discriminator,
                    ).to_json_path()
