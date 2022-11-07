from typing import Callable, List

import pytest  # type:ignore[import]

from maus import (
    DataElementFreeText,
    DataElementValuePool,
    DeepAnwendungshandbuch,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)
from maus.models.anwendungshandbuch import AhbMetaInformation


class TestSearchingInModels:
    """
    Tests regarding the search feature in Edifact Components or AHBs.
    """

    @pytest.mark.parametrize(
        "segment_group,search_predicate,number_of_results",
        [
            pytest.param(
                SegmentGroup(discriminator="SG1", ahb_expression="Foo"),
                lambda _: False,
                0,
                id="always False predicate leads to no results",
            ),
            pytest.param(
                SegmentGroup(discriminator="SG1", ahb_expression="Foo"), lambda _: True, 0, id="no segments, no results"
            ),
            pytest.param(
                SegmentGroup(
                    discriminator="SG1",
                    ahb_expression="Foo",
                    segments=[Segment(discriminator="ASD", data_elements=[], ahb_expression="Foo")],
                ),
                lambda _: True,
                1,
                id="true predicate",
            ),
            pytest.param(
                SegmentGroup(
                    discriminator="SG1",
                    ahb_expression="Foo",
                    segments=[Segment(discriminator="ASD", data_elements=[], ahb_expression="Foo")],
                ),
                lambda seg: seg.discriminator == "ASD",
                1,
                id="matching predicate",
            ),
            pytest.param(
                SegmentGroup(
                    discriminator="SG1",
                    ahb_expression="Foo",
                    segments=[Segment(discriminator="Foo", data_elements=[], ahb_expression="Foo")],
                ),
                lambda seg: seg.discriminator == "Bar",
                0,
                id="not matching predicate",
            ),
            pytest.param(
                SegmentGroup(
                    discriminator="SG1",
                    ahb_expression="Foo",
                    segments=[
                        Segment(discriminator="Foo", data_elements=[], ahb_expression="Foo"),
                        Segment(discriminator="Bar", data_elements=[], ahb_expression="Bar"),
                    ],
                ),
                lambda seg: seg.discriminator == "Bar",
                1,
                id="matching predicate on root level",
            ),
            pytest.param(
                SegmentGroup(
                    discriminator="SG1",
                    ahb_expression="Foo",
                    segments=[
                        Segment(discriminator="abc", ahb_expression="ahb expression", data_elements=[]),
                        Segment(
                            discriminator="abc",
                            ahb_expression="something not ending with expression but foo",
                            data_elements=[],
                        ),
                    ],
                    segment_groups=[
                        SegmentGroup(
                            discriminator="SG2",
                            ahb_expression="Bar",
                            segments=[
                                Segment(discriminator="abc", ahb_expression="ahb expression", data_elements=[]),
                                Segment(discriminator="xyz", ahb_expression="xyz expression", data_elements=[]),
                            ],
                        )
                    ],
                ),
                lambda seg: seg.ahb_expression.endswith("expression"),
                3,
                id="matching predicate with 3 entries",
            ),
        ],
    )
    def test_find_segment_in_segment_group(
        self, segment_group: SegmentGroup, search_predicate: Callable[[Segment], bool], number_of_results: int
    ):
        actual = segment_group.find_segments(search_predicate)
        assert len(actual) == number_of_results

    @pytest.mark.parametrize(
        "deep_ahb,search_predicate,number_of_results",
        [
            pytest.param(
                DeepAnwendungshandbuch(
                    lines=[
                        SegmentGroup(discriminator="SG1", ahb_expression="Foo"),
                        SegmentGroup(
                            discriminator="SG2",
                            ahb_expression="Bar",
                            segment_groups=[SegmentGroup(discriminator="SG3", ahb_expression="Baz")],
                        ),
                    ],
                    meta=AhbMetaInformation(pruefidentifikator="11111"),
                ),
                lambda sg: sg.discriminator == "SG3",
                1,
            ),
            pytest.param(
                DeepAnwendungshandbuch(
                    lines=[
                        SegmentGroup(discriminator="SG1", ahb_expression="Foo"),
                        SegmentGroup(
                            discriminator="SG2",
                            ahb_expression="Bar",
                            segment_groups=[SegmentGroup(discriminator="SG3", ahb_expression="Baz")],
                        ),
                    ],
                    meta=AhbMetaInformation(pruefidentifikator="11111"),
                ),
                lambda sg: sg.discriminator == "SG1",
                1,
            ),
            pytest.param(
                DeepAnwendungshandbuch(
                    lines=[
                        SegmentGroup(discriminator="SG1", ahb_expression="Foo"),
                        SegmentGroup(
                            discriminator="SG2",
                            ahb_expression="Bar",
                            segment_groups=[SegmentGroup(discriminator="SG3", ahb_expression="Baz")],
                        ),
                    ],
                    meta=AhbMetaInformation(pruefidentifikator="11111"),
                ),
                lambda sg: sg.discriminator.startswith("SG"),
                3,
            ),
        ],
    )
    def test_find_segment_group_from_deep_ahb(
        self, deep_ahb: DeepAnwendungshandbuch, search_predicate: Callable[[SegmentGroup], bool], number_of_results: int
    ):
        actual = deep_ahb.find_segment_groups(search_predicate)
        assert len(actual) == number_of_results

    @pytest.mark.parametrize(
        "deep_ahb,group_predicate,segment_predicate,number_of_results",
        [
            pytest.param(
                DeepAnwendungshandbuch(
                    lines=[
                        SegmentGroup(discriminator="SG1", ahb_expression="Foo"),
                        SegmentGroup(
                            discriminator="SG2",
                            ahb_expression="Bar",
                            segment_groups=[
                                SegmentGroup(
                                    discriminator="SG3",
                                    ahb_expression="Baz",
                                    segments=[
                                        Segment(discriminator="abc", ahb_expression="ahb expression", data_elements=[]),
                                        Segment(
                                            discriminator="qwertz", ahb_expression="qwertz expression", data_elements=[]
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                    meta=AhbMetaInformation(pruefidentifikator="11111"),
                ),
                lambda sg: sg.discriminator == "SG3",
                lambda seg: len(seg.discriminator) > 3,
                1,
            ),
        ],
    )
    def test_find_segments_from_deep_ahb(
        self,
        deep_ahb: DeepAnwendungshandbuch,
        group_predicate: Callable[[SegmentGroup], bool],
        segment_predicate: Callable[[Segment], bool],
        number_of_results: int,
    ):
        actual = deep_ahb.find_segments(group_predicate, segment_predicate)
        assert len(actual) == number_of_results

    @pytest.mark.parametrize(
        "deep_ahb, expected_result",
        [
            pytest.param(
                DeepAnwendungshandbuch(
                    meta=AhbMetaInformation(pruefidentifikator="11042"),
                    lines=[
                        SegmentGroup(
                            ahb_expression="expr A",
                            discriminator="disc A",
                            segments=[
                                Segment(
                                    ahb_expression="expr B",
                                    discriminator="disc B",
                                    data_elements=[
                                        DataElementValuePool(
                                            value_pool=[
                                                ValuePoolEntry(
                                                    qualifier="HELLO", meaning="world", ahb_expression="X [1]"
                                                ),
                                                ValuePoolEntry(
                                                    qualifier="MAUS", meaning="rocks", ahb_expression="X [2]"
                                                ),
                                            ],
                                            discriminator="baz",
                                            entered_input="MAUS",
                                            data_element_id="0123",
                                        ),
                                        DataElementFreeText(
                                            ahb_expression="Muss [3]",
                                            entered_input="Hello Mice",
                                            discriminator="bar",
                                            data_element_id="4567",
                                        ),
                                    ],
                                ),
                            ],
                            segment_groups=[],
                        ),
                    ],
                ),
                ["Muss [3]", "X [1]", "X [2]", "expr A", "expr B"],
            )
        ],
    )
    def test_get_all_expressions(self, deep_ahb: DeepAnwendungshandbuch, expected_result: List[str]):
        actual = deep_ahb.get_all_expressions()
        assert actual == expected_result
