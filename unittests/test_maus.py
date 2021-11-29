from typing import List

import pytest  # type:ignore[import]

from maus.maus import merge_lines_with_same_data_element, to_deep_ahb
from maus.models.anwendungshandbuch import (
    AhbLine,
    AhbMetaInformation,
    DeepAnwendungshandbuch,
    DeepAnwendungshandbuchSchema,
    FlatAnwendungshandbuch,
)
from maus.models.edifact_components import DataElement, DataElementFreeText, DataElementValuePool, SegmentGroup
from maus.models.message_implementation_guide import SegmentGroupHierarchy
from unittests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]


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
                        segment_group="SG4",
                        segment="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E01",
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group="SG4",
                        segment="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E02",
                        name="Das Andere",
                        guid=None,
                    ),
                ],
                DataElementValuePool(
                    discriminator="SG4->FOO->0333", value_pool={"E01": "Das Eine", "E02": "Das Andere"}
                ),
            ),
            pytest.param(
                # The following single lines should result in a single DataElement with free text option
                [
                    AhbLine(
                        segment_group="SG4",
                        segment="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry=None,
                        name="Das Eine",
                        guid=None,
                    ),
                ],
                DataElementFreeText(discriminator="SG4->FOO->0333 (Das Eine)", ahb_expression="X", entered_input=None),
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
                        segment_group="SG4",
                        segment="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E01",
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group="SG4",
                        segment="FOO",
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
                        segment_group="SG4",
                        segment="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E01",
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group="SG4",
                        segment="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="E02",
                        name="Das Andere",
                        guid=None,
                    ),
                ],
                DataElementValuePool(
                    discriminator="SG4->FOO->0333", value_pool={"E01": "Das Eine", "E02": "Das Andere"}
                ),
            ),
            pytest.param(
                # The following single lines should result in a single DataElement with free text option
                [
                    AhbLine(
                        segment_group="SG4",
                        segment="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry=None,
                        name="Das Eine",
                        guid=None,
                    ),
                ],
                DataElementFreeText(discriminator="SG4->FOO->0333 (Das Eine)", ahb_expression="X", entered_input=None),
            ),
        ],
    )
    def test_nest_segment_groups_into_each_other(self, ahb_lines: List[AhbLine], expected_data_element: DataElement):
        actual = merge_lines_with_same_data_element(ahb_lines)
        assert actual == expected_data_element

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
                            segment_group=None,
                            segment="UNH",
                            ahb_expression="X",
                            data_element="1234",
                            value_pool_entry=None,
                            name="Nachrichten-Startsegment",
                            guid=None,
                        ),
                        # The following two lines should be merged into a single data element value pool because they
                        # refer to the same data element but have different value pool entries.
                        AhbLine(
                            segment_group="SG4",
                            segment="FOO",
                            ahb_expression="X",
                            data_element="0333",
                            value_pool_entry="E01",
                            name="Das andere",
                            guid=None,
                        ),
                        AhbLine(
                            segment_group="SG4",
                            segment="FOO",
                            ahb_expression="X",
                            data_element="0333",
                            value_pool_entry="E02",
                            name="Das Eine",
                            guid=None,
                        ),
                        AhbLine(
                            segment_group="SG5",
                            segment="BAR",
                            ahb_expression="X",
                            data_element="1234",
                            name="Die fünfte Gruppe",
                            guid=None,
                            value_pool_entry=None,
                        ),
                        AhbLine(
                            segment_group="SG6",
                            segment="irgendwas",
                            ahb_expression="X",
                            data_element="7889",
                            name="Die sechste Gruppe",
                            guid=None,
                            value_pool_entry=None,
                        ),
                        AhbLine(
                            segment_group="SG7",
                            segment="ASD",
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
                            discriminator=None,
                            ahb_expression="X",
                            segments=[
                                DataElementFreeText(
                                    discriminator="UNH->1234 (Nachrichten-Startsegment)",
                                    ahb_expression="X",
                                    entered_input=None,
                                )
                            ],
                            segment_groups=[
                                SegmentGroup(
                                    discriminator="SG4",
                                    ahb_expression="X",
                                    segments=[
                                        DataElementValuePool(
                                            discriminator="SG4->FOO->0333",
                                            value_pool={"E01": "Das andere", "E02": "Das Eine"},
                                        )
                                    ],
                                    segment_groups=[
                                        SegmentGroup(
                                            discriminator="SG5",
                                            ahb_expression="X",
                                            segments=[
                                                DataElementFreeText(
                                                    discriminator="SG5->BAR->1234 (Die fünfte Gruppe)",
                                                    ahb_expression="X",
                                                    entered_input=None,
                                                )
                                            ],
                                            segment_groups=[
                                                SegmentGroup(
                                                    discriminator="SG6",
                                                    ahb_expression="X",
                                                    segments=[
                                                        DataElementFreeText(
                                                            discriminator="SG6->irgendwas->7889 (Die sechste Gruppe)",
                                                            ahb_expression="X",
                                                            entered_input=None,
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
                                                DataElementFreeText(
                                                    discriminator="SG7->ASD->0123 (Die siebte Gruppe)",
                                                    ahb_expression="X",
                                                    entered_input=None,
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
