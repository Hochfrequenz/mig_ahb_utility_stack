import pytest  # type:ignore[import]

from maus.models.edifact_components import (
    DataElementFreeText,
    DataElementFreeTextSchema,
    DataElementValuePool,
    DataElementValuePoolSchema,
    EdifactStack,
    EdifactStackLevel,
    Segment,
    SegmentGroup,
    SegmentGroupSchema,
    SegmentSchema,
)
from unittests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]


class TestEdifactComponents:
    """
    Tests the behaviour of the Edifact Components
    """

    @pytest.mark.parametrize(
        "free_text, expected_json_dict",
        [
            pytest.param(
                DataElementFreeText(ahb_expression="Muss [1]", entered_input="Hello Maus", discriminator="foo"),
                {"ahb_expression": "Muss [1]", "entered_input": "Hello Maus", "discriminator": "foo"},
            ),
        ],
    )
    def test_free_text_serialization_roundtrip(self, free_text: DataElementFreeText, expected_json_dict: dict):
        assert_serialization_roundtrip(free_text, DataElementFreeTextSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "value_pool, expected_json_dict",
        [
            pytest.param(
                DataElementValuePool(value_pool={"hello": "world", "maus": "rocks"}, discriminator="foo"),
                {"value_pool": {"hello": "world", "maus": "rocks"}, "discriminator": "foo"},
            ),
        ],
    )
    def test_value_pool_serialization_roundtrip(self, value_pool: DataElementValuePool, expected_json_dict: dict):
        assert_serialization_roundtrip(value_pool, DataElementValuePoolSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "segment, expected_json_dict",
        [
            pytest.param(
                Segment(
                    ahb_expression="X",
                    data_elements=[
                        DataElementValuePool(value_pool={"hello": "world", "maus": "rocks"}, discriminator="baz"),
                        DataElementFreeText(ahb_expression="Muss [1]", entered_input="Hello Maus", discriminator="bar"),
                    ],
                    discriminator="foo",
                ),
                {
                    "ahb_expression": "X",
                    "data_elements": [
                        {"value_pool": {"hello": "world", "maus": "rocks"}, "discriminator": "baz"},
                        {"ahb_expression": "Muss [1]", "entered_input": "Hello Maus", "discriminator": "bar"},
                    ],
                    "discriminator": "foo",
                },
            ),
        ],
    )
    def test_segment_serialization_roundtrip(self, segment: Segment, expected_json_dict: dict):
        assert_serialization_roundtrip(segment, SegmentSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "segment_group, expected_json_dict",
        [
            pytest.param(
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
                {
                    "ahb_expression": "expr A",
                    "discriminator": "disc A",
                    "segments": [
                        {
                            "ahb_expression": "expr B",
                            "discriminator": "disc B",
                            "data_elements": [
                                {"value_pool": {"hello": "world", "maus": "rocks"}, "discriminator": "baz"},
                                {"ahb_expression": "Muss [1]", "entered_input": "Hello Maus", "discriminator": "bar"},
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
            ),
        ],
    )
    def test_segment_group_serialization_roundtrip(self, segment_group: SegmentGroup, expected_json_dict: dict):
        assert_serialization_roundtrip(segment_group, SegmentGroupSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "stack_x, stack_y, x_is_sub_stack_of_y, x_is_parent_of_y",
        [
            pytest.param(EdifactStack(levels=[]), EdifactStack(levels=[]), True, True, id="equality"),
            pytest.param(
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=False)]),
                EdifactStack(levels=[]),
                True,
                False,
                id="any stack is sub stack of root",
            ),
            pytest.param(
                EdifactStack(levels=[]),
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=False)]),
                False,
                True,
                id="other too deep",
            ),
            pytest.param(
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=True)]),
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=False)]),
                False,
                False,
                id="different groubability",
            ),
            pytest.param(
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=True)]),
                EdifactStack(levels=[EdifactStackLevel(name="y", is_groupable=True)]),
                False,
                False,
                id="different name",
            ),
            pytest.param(
                EdifactStack(
                    levels=[
                        EdifactStackLevel(name="a", is_groupable=True),
                        EdifactStackLevel(name="b", is_groupable=True),
                    ]
                ),
                EdifactStack(levels=[EdifactStackLevel(name="a", is_groupable=True)]),
                True,
                False,
                id="yes",
            ),
        ],
    )
    def test_edifact_stack_is_sub_or_parent_of(
        self, stack_x: EdifactStack, stack_y: EdifactStack, x_is_sub_stack_of_y: bool, x_is_parent_of_y: bool
    ):
        assert stack_x.is_sub_stack_of(stack_y) == x_is_sub_stack_of_y
        assert stack_x.is_parent_of(stack_y) == x_is_parent_of_y
