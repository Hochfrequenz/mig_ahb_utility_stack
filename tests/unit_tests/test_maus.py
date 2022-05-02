from typing import List

import pytest  # type:ignore[import]

from maus import group_lines_by_segment_group, merge_lines_with_same_data_element, to_deep_ahb
from maus.models.anwendungshandbuch import AhbLine, AhbMetaInformation, DeepAnwendungshandbuch, FlatAnwendungshandbuch
from maus.models.edifact_components import (
    DataElement,
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)
from maus.models.message_implementation_guide import SegmentGroupHierarchy
from serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]


class TestMaus:
    """
    Tests the behaviour of the MAUS.
    """

    @pytest.mark.parametrize(
        "ahb_lines, expected_data_element",
        [
            pytest.param(
                # The following two lines should be merged into a single data element value pool because they
                # refer to the same data element but have different value pool entries.
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E01",
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E02",
                        name="Das Andere",
                        guid=None,
                    ),
                ],
                DataElementValuePool(
                    discriminator="SG4->FOO->0333",
                    value_pool=[
                        ValuePoolEntry(
                            qualifier="E01",
                            meaning="Das Eine",
                            ahb_expression="X",
                        ),
                        ValuePoolEntry(
                            qualifier="E02",
                            meaning="Das Andere",
                            ahb_expression="X",
                        ),
                    ],
                    data_element_id="0333",
                ),
            ),
            pytest.param(
                # The following single lines should result in a single DataElement with free text option
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry=None,
                        name="Das Eine",
                        guid=None,
                    ),
                ],
                DataElementFreeText(
                    discriminator="Das Eine",
                    ahb_expression="X",
                    entered_input=None,
                    data_element_id="0333",
                ),
            ),
        ],
    )
    def test_data_element_merging(self, ahb_lines: List[AhbLine], expected_data_element: DataElement):
        actual = merge_lines_with_same_data_element(ahb_lines)
        assert actual == expected_data_element

    @pytest.mark.parametrize(
        "ahb_lines",
        [
            pytest.param(
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E01",
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0334",
                        value_pool_entry="E02",
                        name="Das Andere",
                        guid=None,
                    ),
                ],
                id="lines with different data element",
            ),
            pytest.param([], id="empty list"),
        ],
    )
    def test_data_element_value_error(self, ahb_lines: List[AhbLine]):
        with pytest.raises(ValueError):
            merge_lines_with_same_data_element(ahb_lines)

    @pytest.mark.parametrize(
        "ahb_lines, expected_data_element",
        [
            pytest.param(
                # The following two lines should be merged into a single data element value pool because they
                # refer to the same data element but have different value pool entries.
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E01",
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E02",
                        name="Das Andere",
                        guid=None,
                    ),
                ],
                DataElementValuePool(
                    discriminator="SG4->FOO->0333",
                    value_pool=[
                        ValuePoolEntry(
                            qualifier="E01",
                            meaning="Das Eine",
                            ahb_expression="X",
                        ),
                        ValuePoolEntry(
                            qualifier="E02",
                            meaning="Das Andere",
                            ahb_expression="X",
                        ),
                    ],
                    data_element_id="0333",
                ),
            ),
            pytest.param(
                # The following single lines should result in a single DataElement with free text option
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry=None,
                        name="Das Eine",
                        guid=None,
                    ),
                ],
                DataElementFreeText(
                    discriminator="Das Eine",
                    ahb_expression="X",
                    entered_input=None,
                    data_element_id="0333",
                ),
            ),
        ],
    )
    def test_nest_segment_groups_into_each_other(self, ahb_lines: List[AhbLine], expected_data_element: DataElement):
        actual = merge_lines_with_same_data_element(ahb_lines)
        assert actual == expected_data_element

    @pytest.mark.parametrize(
        "ahb_lines, sgh, expected_result",
        [
            pytest.param(
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E01",
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E02",
                        name="Das Andere",
                        guid=None,
                    ),
                ],
                SegmentGroupHierarchy(segment_group="SG4", sub_hierarchy=None, opening_segment="FOO"),
                [
                    SegmentGroup(
                        discriminator="SG4",
                        ahb_expression="X",
                        segments=[
                            Segment(
                                discriminator="FOO",
                                ahb_expression="X",
                                data_elements=[
                                    DataElementValuePool(
                                        discriminator="SG4->FOO->0333",
                                        value_pool=[
                                            ValuePoolEntry(
                                                qualifier="E01",
                                                meaning="Das Eine",
                                                ahb_expression="X",
                                            ),
                                            ValuePoolEntry(
                                                qualifier="E02",
                                                meaning="Das Andere",
                                                ahb_expression="X",
                                            ),
                                        ],
                                        data_element_id="0333",
                                    )
                                ],
                            )
                        ],
                        segment_groups=[],
                    )
                ],
            ),
            pytest.param(
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E01",
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E02",
                        name="Das Andere",
                        guid=None,
                    ),
                ],
                SegmentGroupHierarchy(segment_group="SG4", sub_hierarchy=None, opening_segment="FOO"),
                [
                    SegmentGroup(
                        discriminator="SG4",
                        ahb_expression="X",
                        segments=[
                            Segment(
                                discriminator="FOO",
                                ahb_expression="X",
                                data_elements=[
                                    DataElementValuePool(
                                        discriminator="SG4->FOO->0333",
                                        value_pool=[
                                            ValuePoolEntry(
                                                qualifier="E01",
                                                meaning="Das Eine",
                                                ahb_expression="X",
                                            ),
                                            ValuePoolEntry(
                                                qualifier="E02",
                                                meaning="Das Andere",
                                                ahb_expression="X",
                                            ),
                                        ],
                                        data_element_id="0333",
                                    )
                                ],
                            )
                        ],
                        segment_groups=[],
                    )
                ],
            ),
        ],
    )
    def test_group_lines_by_segment_group(
        self, ahb_lines: List[AhbLine], sgh: SegmentGroupHierarchy, expected_result: List[SegmentGroup]
    ):
        actual = group_lines_by_segment_group(ahb_lines, sgh)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "sgh, flat_ahb, expected_deep",
        [
            pytest.param(
                SegmentGroupHierarchy(
                    segment_group=None,
                    opening_segment="UNH",
                    sub_hierarchy=[
                        SegmentGroupHierarchy(
                            segment_group="SG4",
                            opening_segment="FOO",
                            sub_hierarchy=[
                                SegmentGroupHierarchy(
                                    segment_group="SG5",
                                    opening_segment="BAR",
                                    sub_hierarchy=[
                                        SegmentGroupHierarchy(
                                            segment_group="SG6", opening_segment="BAZ", sub_hierarchy=None
                                        )
                                    ],
                                ),
                                SegmentGroupHierarchy(
                                    segment_group="SG7",
                                    opening_segment="ASD",
                                    sub_hierarchy=[
                                        SegmentGroupHierarchy(
                                            segment_group="SG8", opening_segment="YXC", sub_hierarchy=None
                                        )
                                    ],
                                ),
                            ],
                        )
                    ],
                ),
                FlatAnwendungshandbuch(
                    meta=AhbMetaInformation(pruefidentifikator="12345"),
                    lines=[
                        # this segment should stay at the beginning, alone
                        AhbLine(
                            segment_group_key=None,
                            segment_code="UNH",
                            ahb_expression="X",
                            data_element="1234",
                            value_pool_entry=None,
                            name="Nachrichten-Startsegment",
                            guid=None,
                        ),
                        # The following two lines should be merged into a single data element value pool because they
                        # refer to the same data element but have different value pool entries.
                        AhbLine(
                            segment_group_key="SG4",
                            segment_code="FOO",
                            ahb_expression="X",
                            data_element="0333",
                            value_pool_entry="E01",
                            name="Das andere",
                            guid=None,
                        ),
                        AhbLine(
                            segment_group_key="SG4",
                            segment_code="FOO",
                            ahb_expression="X",
                            data_element="0333",
                            value_pool_entry="E02",
                            name="Das Eine",
                            guid=None,
                        ),
                        AhbLine(
                            segment_group_key="SG5",
                            segment_code="BAR",
                            ahb_expression="X",
                            data_element="1234",
                            name="Die fünfte Gruppe",
                            guid=None,
                            value_pool_entry=None,
                        ),
                        AhbLine(
                            segment_group_key="SG6",
                            segment_code="irgendwas",
                            ahb_expression="X",
                            data_element="7889",
                            name="Die sechste Gruppe",
                            guid=None,
                            value_pool_entry=None,
                        ),
                        AhbLine(
                            segment_group_key="SG7",
                            segment_code="ASD",
                            ahb_expression="X",
                            data_element="0123",
                            name="Die siebte Gruppe",
                            guid=None,
                            value_pool_entry=None,
                        ),
                        # die achte fehlt
                    ],
                ),
                DeepAnwendungshandbuch(
                    meta=AhbMetaInformation(pruefidentifikator="12345"),
                    lines=[
                        SegmentGroup(
                            discriminator="root",
                            ahb_expression="X",
                            segments=[
                                Segment(
                                    discriminator="UNH",
                                    ahb_expression="X",
                                    data_elements=[
                                        DataElementFreeText(
                                            discriminator="Nachrichten-Startsegment",
                                            ahb_expression="X",
                                            entered_input=None,
                                            data_element_id="1234",
                                        )
                                    ],
                                )
                            ],
                            segment_groups=[
                                SegmentGroup(
                                    discriminator="SG4",
                                    ahb_expression="X",
                                    segments=[
                                        Segment(
                                            discriminator="FOO",
                                            ahb_expression="X",
                                            data_elements=[
                                                DataElementValuePool(
                                                    discriminator="SG4->FOO->0333",
                                                    value_pool=[
                                                        ValuePoolEntry(
                                                            qualifier="E01",
                                                            meaning="Das andere",
                                                            ahb_expression="X",
                                                        ),
                                                        ValuePoolEntry(
                                                            qualifier="E02",
                                                            meaning="Das Eine",
                                                            ahb_expression="X",
                                                        ),
                                                    ],
                                                    data_element_id="0333",
                                                )
                                            ],
                                        )
                                    ],
                                    segment_groups=[
                                        SegmentGroup(
                                            discriminator="SG5",
                                            ahb_expression="X",
                                            segments=[
                                                Segment(
                                                    discriminator="BAR",
                                                    ahb_expression="X",
                                                    data_elements=[
                                                        DataElementFreeText(
                                                            discriminator="Die fünfte Gruppe",
                                                            ahb_expression="X",
                                                            entered_input=None,
                                                            data_element_id="1234",
                                                        )
                                                    ],
                                                )
                                            ],
                                            segment_groups=[
                                                SegmentGroup(
                                                    discriminator="SG6",
                                                    ahb_expression="X",
                                                    segments=[
                                                        Segment(
                                                            discriminator="irgendwas",
                                                            ahb_expression="X",
                                                            data_elements=[
                                                                DataElementFreeText(
                                                                    discriminator="Die sechste Gruppe",
                                                                    ahb_expression="X",
                                                                    entered_input=None,
                                                                    data_element_id="7889",
                                                                )
                                                            ],
                                                        )
                                                    ],
                                                    segment_groups=[],
                                                )
                                            ],
                                        ),
                                        SegmentGroup(
                                            discriminator="SG7",
                                            ahb_expression="X",
                                            segments=[
                                                Segment(
                                                    discriminator="ASD",
                                                    ahb_expression="X",
                                                    data_elements=[
                                                        DataElementFreeText(
                                                            discriminator="Die siebte Gruppe",
                                                            ahb_expression="X",
                                                            entered_input=None,
                                                            data_element_id="0123",
                                                        )
                                                    ],
                                                )
                                            ],
                                            segment_groups=[],
                                        ),
                                    ],
                                )
                            ],
                        )
                    ],
                ),
            ),
        ],
    )
    def test_ahb_flat_to_deep(
        self, sgh: SegmentGroupHierarchy, flat_ahb: FlatAnwendungshandbuch, expected_deep: DeepAnwendungshandbuch
    ):
        actual = to_deep_ahb(flat_ahb, sgh)
        # actual_json = DeepAnwendungshandbuchSchema().dumps(actual)
        assert actual == expected_deep
