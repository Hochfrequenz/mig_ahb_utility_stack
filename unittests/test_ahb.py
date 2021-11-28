import uuid
from typing import List, Optional, Set

import pytest  # type:ignore[import]

from maus.models.anwendungshandbuch import (
    AhbLine,
    AhbLineSchema,
    AhbMetaInformation,
    AhbMetaInformationSchema,
    DeepAnwendungshandbuch,
    DeepAnwendungshandbuchSchema,
    FlatAnwendungshandbuch,
    FlatAnwendungshandbuchSchema,
)
from maus.models.edifact_components import DataElementFreeText, DataElementValuePool, Segment, SegmentGroup
from unittests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]


class TestAhb:
    """
    Tests the behaviour of the Anwendungshandbuch model
    """

    @pytest.mark.parametrize(
        "ahb, expected_json_dict",
        [
            pytest.param(
                AhbMetaInformation(
                    pruefidentifikator="11042",
                ),
                {
                    "pruefidentifikator": "11042",
                },
            ),
        ],
    )
    def test_ahb_meta_information_serialization_roundtrip(self, ahb: AhbMetaInformation, expected_json_dict: dict):
        assert_serialization_roundtrip(ahb, AhbMetaInformationSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "ahb_line, expected_json_dict",
        [
            pytest.param(
                AhbLine(
                    ahb_expression="Muss [1] O [2]",
                    segment_group="SG2",
                    segment="NAD",
                    data_element="3039",
                    value_pool_entry="E01",
                    name="MP-ID",
                    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                ),
                {
                    "ahb_expression": "Muss [1] O [2]",
                    "segment_group": "SG2",
                    "segment": "NAD",
                    "data_element": "3039",
                    "value_pool_entry": "E01",
                    "name": "MP-ID",
                    "guid": "12b1a98a-edf5-4177-89e5-a6d8a92c5fdc",
                },
            ),
        ],
    )
    def test_ahbline_serialization_roundtrip(self, ahb_line: AhbLine, expected_json_dict: dict):
        assert_serialization_roundtrip(ahb_line, AhbLineSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "ahb_line, include_name, expected_discriminator",
        [
            pytest.param(
                AhbLine(
                    ahb_expression="Muss [1] O [2]",
                    segment_group="SG2",
                    segment="NAD",
                    data_element="3039",
                    value_pool_entry="E01",
                    name="MP-ID",
                    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                ),
                True,
                "SG2->NAD->3039 (MP-ID)",
            ),
            pytest.param(
                AhbLine(
                    ahb_expression="Muss [1] O [2]",
                    segment_group="SG2",
                    segment="NAD",
                    data_element="3039",
                    value_pool_entry="E01",
                    name="MP-ID",
                    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                ),
                False,
                "SG2->NAD->3039",
            ),
            pytest.param(
                AhbLine(
                    ahb_expression="Muss [1] O [2]",
                    segment_group=None,
                    segment="UNH",
                    data_element="0062",
                    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                    value_pool_entry=None,
                    name=None,
                ),
                True,
                "UNH->0062",
            ),
        ],
    )
    def test_ahbline_get_discriminator(self, ahb_line: AhbLine, include_name: bool, expected_discriminator: str):
        actual = ahb_line.get_discriminator(include_name)
        assert actual == expected_discriminator

    @pytest.mark.parametrize(
        "flat_ahb, expected_json_dict",
        [
            pytest.param(
                FlatAnwendungshandbuch(
                    meta=AhbMetaInformation(pruefidentifikator="11042"),
                    lines=[
                        AhbLine(
                            ahb_expression="Muss [1] O [2]",
                            segment_group="SG2",
                            segment="NAD",
                            data_element="3039",
                            value_pool_entry="E01",
                            name="MP-ID",
                            guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                        )
                    ],
                ),
                {
                    "meta": {"pruefidentifikator": "11042"},
                    "lines": [
                        {
                            "ahb_expression": "Muss [1] O [2]",
                            "segment_group": "SG2",
                            "segment": "NAD",
                            "data_element": "3039",
                            "value_pool_entry": "E01",
                            "name": "MP-ID",
                            "guid": "12b1a98a-edf5-4177-89e5-a6d8a92c5fdc",
                        }
                    ],
                },
            ),
        ],
    )
    def test_flatahb_serialization_roundtrip(self, flat_ahb: FlatAnwendungshandbuch, expected_json_dict: dict):
        assert_serialization_roundtrip(flat_ahb, FlatAnwendungshandbuchSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "deep_ahb, expected_json_dict",
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
                                            value_pool={"hello": "world", "maus": "rocks"}, discriminator="baz"
                                        ),
                                        DataElementFreeText(
                                            ahb_expression="Muss [1]", entered_input="Hello Maus", discriminator="bar"
                                        ),
                                    ],
                                ),
                            ],
                            segment_groups=[
                                SegmentGroup(
                                    discriminator="disc C",
                                    ahb_expression="expr C",
                                    segments=[
                                        Segment(
                                            ahb_expression="expr Y",
                                            discriminator="disc Y",
                                            data_elements=[],
                                        )
                                    ],
                                    segment_groups=None,
                                ),
                            ],
                        ),
                    ],
                ),
                {
                    "meta": {"pruefidentifikator": "11042"},
                    "lines": [
                        {
                            "ahb_expression": "expr A",
                            "discriminator": "disc A",
                            "segments": [
                                {
                                    "ahb_expression": "expr B",
                                    "discriminator": "disc B",
                                    "data_elements": [
                                        {"value_pool": {"hello": "world", "maus": "rocks"}, "discriminator": "baz"},
                                        {
                                            "ahb_expression": "Muss [1]",
                                            "entered_input": "Hello Maus",
                                            "discriminator": "bar",
                                        },
                                    ],
                                }
                            ],
                            "segment_groups": [
                                {
                                    "ahb_expression": "expr C",
                                    "discriminator": "disc C",
                                    "segments": [
                                        {
                                            "ahb_expression": "expr Y",
                                            "discriminator": "disc Y",
                                            "data_elements": [],
                                        }
                                    ],
                                    "segment_groups": None,
                                }
                            ],
                        },
                    ],
                },
            ),
        ],
    )
    def test_deepahb_serialization_roundtrip(self, deep_ahb: DeepAnwendungshandbuch, expected_json_dict: dict):
        assert_serialization_roundtrip(deep_ahb, DeepAnwendungshandbuchSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "lines, expected_group_names",
        [
            pytest.param(
                [
                    AhbLine(
                        segment_group="Foo",
                        guid=None,
                        segment=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group="Bar",
                        guid=None,
                        segment=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group=None,
                        guid=None,
                        segment=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group="Bar",
                        guid=None,
                        segment=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                ],
                {"Foo", "Bar", None},
            )
        ],
    )
    def test_get_segment_groups(self, lines: List[AhbLine], expected_group_names: Set[Optional[str]]):
        actual = FlatAnwendungshandbuch._get_available_segment_groups(lines)
        assert actual == expected_group_names
