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
from maus.models.edifact_components import (
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)
from unittests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]

meta_x = AhbMetaInformation(
    pruefidentifikator="11042",
)
meta_y = AhbMetaInformation(
    pruefidentifikator="11043",
)

line_x = AhbLine(
    ahb_expression="Muss [1] O [2]",
    segment_group_key="SG2",
    segment_code="NAD",
    data_element="3039",
    value_pool_entry="E01",
    name="MP-ID",
    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
)
line_y = AhbLine(
    ahb_expression="Muss [3] O [4]",
    segment_group_key="SG2",
    segment_code="NAD",
    data_element="3039",
    value_pool_entry="E01",
    name="MP-ID",
    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
)


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
        "ahb_x, ahb_y, are_equal",
        [
            pytest.param(meta_x, AhbMetaInformationSchema().loads(AhbMetaInformationSchema().dumps(meta_x)), True),
            pytest.param(meta_x, meta_y, False),
        ],
    )
    def test_ahb_meta_information_equality(self, ahb_x: AhbMetaInformation, ahb_y: AhbMetaInformation, are_equal: bool):
        actual = ahb_x == ahb_y
        assert actual == are_equal

    @pytest.mark.parametrize(
        "ahb_line, expected_json_dict",
        [
            pytest.param(
                AhbLine(
                    ahb_expression="Muss [1] O [2]",
                    segment_group_key="SG2",
                    segment_code="NAD",
                    data_element="3039",
                    value_pool_entry="E01",
                    name="MP-ID",
                    section_name="Foo",
                    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                ),
                {
                    "ahb_expression": "Muss [1] O [2]",
                    "segment_group_key": "SG2",
                    "segment_code": "NAD",
                    "data_element": "3039",
                    "value_pool_entry": "E01",
                    "name": "MP-ID",
                    "guid": "12b1a98a-edf5-4177-89e5-a6d8a92c5fdc",
                    "section_name": "Foo",
                },
            ),
        ],
    )
    def test_ahbline_serialization_roundtrip(self, ahb_line: AhbLine, expected_json_dict: dict):
        assert_serialization_roundtrip(ahb_line, AhbLineSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "line_x, line_y, are_equal",
        [
            pytest.param(line_x, AhbLineSchema().loads(AhbLineSchema().dumps(line_x)), True),
            pytest.param(line_x, line_y, False),
        ],
    )
    def test_ahb_line_equality(self, line_x: AhbLine, line_y: AhbLine, are_equal: bool):
        actual = line_x == line_y
        assert actual == are_equal

    @pytest.mark.parametrize(
        "ahb_line, expected_holds_any_information",
        [
            pytest.param(
                AhbLine(
                    ahb_expression="Muss [1] O [2]",
                    segment_group_key="SG2",
                    segment_code="NAD",
                    data_element="3039",
                    value_pool_entry="E01",
                    name="MP-ID",
                    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                ),
                True,
            ),
            pytest.param(
                AhbLine(
                    ahb_expression=None,
                    segment_group_key=None,
                    segment_code=None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                ),
                False,
            ),
            pytest.param(
                AhbLine(
                    ahb_expression=" ",
                    segment_group_key="",
                    segment_code="",
                    data_element="   ",
                    value_pool_entry="",
                    name="",
                    guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                ),
                False,
            ),
        ],
    )
    def test_ahbline_holds_any_information(self, ahb_line: AhbLine, expected_holds_any_information: bool):
        actual = ahb_line.holds_any_information()
        assert actual == expected_holds_any_information

    @pytest.mark.parametrize(
        "ahb_line, include_name, expected_discriminator",
        [
            pytest.param(
                AhbLine(
                    ahb_expression="Muss [1] O [2]",
                    segment_group_key="SG2",
                    segment_code="NAD",
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
                    segment_group_key="SG2",
                    segment_code="NAD",
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
                    segment_group_key=None,
                    segment_code="UNH",
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
                            segment_group_key="SG2",
                            segment_code="NAD",
                            data_element="3039",
                            value_pool_entry="E01",
                            name="MP-ID",
                            guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                            section_name="MP-ID Absender",
                        )
                    ],
                ),
                {
                    "meta": {"pruefidentifikator": "11042"},
                    "lines": [
                        {
                            "ahb_expression": "Muss [1] O [2]",
                            "segment_group_key": "SG2",
                            "segment_code": "NAD",
                            "data_element": "3039",
                            "value_pool_entry": "E01",
                            "name": "MP-ID",
                            "guid": "12b1a98a-edf5-4177-89e5-a6d8a92c5fdc",
                            "section_name": "MP-ID Absender",
                        }
                    ],
                },
            ),
        ],
    )
    def test_flatahb_serialization_roundtrip(self, flat_ahb: FlatAnwendungshandbuch, expected_json_dict: dict):
        assert_serialization_roundtrip(flat_ahb, FlatAnwendungshandbuchSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "ahb_x, ahb_y, are_equal",
        [
            pytest.param(
                FlatAnwendungshandbuch(
                    meta=meta_x,
                    lines=[line_x],
                ),
                FlatAnwendungshandbuch(
                    meta=meta_x,
                    lines=[line_x],
                ),
                True,
            ),
            pytest.param(
                FlatAnwendungshandbuch(
                    meta=meta_x,
                    lines=[line_x],
                ),
                FlatAnwendungshandbuch(
                    meta=meta_y,
                    lines=[line_x],
                ),
                False,
                id="different meta",
            ),
            pytest.param(
                FlatAnwendungshandbuch(
                    meta=meta_x,
                    lines=[line_x],
                ),
                FlatAnwendungshandbuch(
                    meta=meta_x,
                    lines=[line_y],
                ),
                False,
                id="different line",
            ),
        ],
    )
    def test_flat_ahb_equality(self, ahb_x: FlatAnwendungshandbuch, ahb_y: FlatAnwendungshandbuch, are_equal: bool):
        actual = ahb_x == ahb_y
        assert actual == are_equal

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
                                    section_name="foo",
                                    data_elements=[
                                        DataElementValuePool(
                                            value_pool=[
                                                ValuePoolEntry(qualifier="hello", meaning="world", ahb_expression="X"),
                                                ValuePoolEntry(qualifier="maus", meaning="rocks", ahb_expression="X"),
                                            ],
                                            discriminator="baz",
                                            data_element_id="0123",
                                        ),
                                        DataElementFreeText(
                                            ahb_expression="Muss [1]",
                                            entered_input="Hello Maus",
                                            discriminator="bar",
                                            data_element_id="4567",
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
                                            section_name="bar",
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
                                    "section_name": "foo",
                                    "ahb_expression": "expr B",
                                    "discriminator": "disc B",
                                    "data_elements": [
                                        {
                                            "value_pool": [
                                                {"qualifier": "hello", "meaning": "world", "ahb_expression": "X"},
                                                {"qualifier": "maus", "meaning": "rocks", "ahb_expression": "X"},
                                            ],
                                            "discriminator": "baz",
                                            "data_element_id": "0123",
                                            "value_type": "VALUE_POOL",
                                        },
                                        {
                                            "ahb_expression": "Muss [1]",
                                            "entered_input": "Hello Maus",
                                            "discriminator": "bar",
                                            "data_element_id": "4567",
                                            "value_type": "TEXT",
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
                                            "section_name": "bar",
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
    def test_deep_ahb_serialization_roundtrip(self, deep_ahb: DeepAnwendungshandbuch, expected_json_dict: dict):
        assert_serialization_roundtrip(deep_ahb, DeepAnwendungshandbuchSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "ahb_x, ahb_y, are_equal",
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
                                                ValuePoolEntry(qualifier="hello", meaning="world", ahb_expression="X"),
                                                ValuePoolEntry(qualifier="maus", meaning="rocks", ahb_expression="X"),
                                            ],
                                            discriminator="baz",
                                            data_element_id="0123",
                                        ),
                                        DataElementFreeText(
                                            ahb_expression="Muss [1]",
                                            entered_input="Hello Maus",
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
                                                ValuePoolEntry(qualifier="hello", meaning="world", ahb_expression="X"),
                                                ValuePoolEntry(qualifier="maus", meaning="rocks", ahb_expression="X"),
                                            ],
                                            discriminator="baz",
                                            data_element_id="0123",
                                        ),
                                        DataElementFreeText(
                                            ahb_expression="Muss [1]",
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
                False,
                id="different lines",
            ),
        ],
    )
    def test_deep_ahb_equality(self, ahb_x: DeepAnwendungshandbuch, ahb_y: DeepAnwendungshandbuch, are_equal: bool):
        actual = ahb_x == ahb_y
        assert actual == are_equal

    @pytest.mark.parametrize(
        "lines, expected_group_names",
        [
            pytest.param(
                [
                    AhbLine(
                        segment_group_key="Foo",
                        guid=None,
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key="Bar",
                        guid=None,
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key=None,
                        guid=None,
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key="Bar",
                        guid=None,
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                ],
                ["Foo", "Bar", None],
            )
        ],
    )
    def test_get_segment_groups(self, lines: List[AhbLine], expected_group_names: Set[Optional[str]]):
        actual = FlatAnwendungshandbuch._get_available_segment_groups(lines)
        assert actual == expected_group_names

    @pytest.mark.parametrize(
        "unsorted_input, sg_order, expected_result",
        [
            pytest.param(
                [
                    AhbLine(
                        segment_group_key="Foo",
                        guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key="Bar",
                        guid=uuid.UUID("9ec5ddb3-3721-48be-9d57-8742e08aa7cf"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key=None,
                        guid=uuid.UUID("7beb2471-0fd2-4b6b-8aae-a5d1f153972d"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key="Bar",
                        guid=uuid.UUID("365e1f9d-0bb9-43ab-921b-9ffa16b6df86"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key="Foo",
                        guid=uuid.UUID("8874a7c9-0143-4aa5-b7fe-5225bb25d2c5"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                ],
                ["Foo", "Bar", None],
                [
                    AhbLine(
                        segment_group_key="Foo",
                        guid=uuid.UUID("12b1a98a-edf5-4177-89e5-a6d8a92c5fdc"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key="Foo",
                        guid=uuid.UUID("8874a7c9-0143-4aa5-b7fe-5225bb25d2c5"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key="Bar",
                        guid=uuid.UUID("9ec5ddb3-3721-48be-9d57-8742e08aa7cf"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key="Bar",
                        guid=uuid.UUID("365e1f9d-0bb9-43ab-921b-9ffa16b6df86"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                    AhbLine(
                        segment_group_key=None,
                        guid=uuid.UUID("7beb2471-0fd2-4b6b-8aae-a5d1f153972d"),
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        ahb_expression=None,
                        name=None,
                    ),
                ],
            )
        ],
    )
    def test_sorted_segment_groups(
        self, unsorted_input: List[AhbLine], sg_order: List[Optional[str]], expected_result: List[AhbLine]
    ):
        actual = FlatAnwendungshandbuch._sorted_lines_by_segment_groups(unsorted_input, sg_order)
        assert actual == expected_result
