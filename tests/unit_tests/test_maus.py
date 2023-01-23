from typing import List

import pytest  # type:ignore[import]
from unit_tests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]

from maus.mig_ahb_matching import merge_lines_with_same_data_element
from maus.models.anwendungshandbuch import AhbLine
from maus.models.edifact_components import (
    DataElement,
    DataElementFreeText,
    DataElementValuePool,
    EdifactStack,
    ValuePoolEntry,
)


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
                    discriminator="$",
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
                    entered_input=None,
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
                    discriminator="$",
                    ahb_expression="X",
                    entered_input=None,
                    data_element_id="0333",
                ),
            ),
        ],
    )
    def test_data_element_merging(self, ahb_lines: List[AhbLine], expected_data_element: DataElement):
        actual = merge_lines_with_same_data_element(ahb_lines, EdifactStack(levels=[]))
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
            merge_lines_with_same_data_element(ahb_lines, EdifactStack(levels=[]))

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
                    discriminator="$",
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
                    entered_input=None,
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
                    discriminator="$",
                    ahb_expression="X",
                    entered_input=None,
                    data_element_id="0333",
                ),
            ),
        ],
    )
    def test_nest_segment_groups_into_each_other(self, ahb_lines: List[AhbLine], expected_data_element: DataElement):
        actual = merge_lines_with_same_data_element(ahb_lines, EdifactStack(levels=[]))
        assert actual == expected_data_element
