from typing import Dict, List, Optional, Tuple
from uuid import UUID

import pytest  # type:ignore[import]
from jsonpath_ng.ext import parse  # type:ignore[import] #  jsonpath is just installed in the tests
from more_itertools import last

from maus.models.anwendungshandbuch import AhbLine, _remove_grouped_ahb_lines_containing_section_name
from maus.models.message_implementation_guide import SegmentGroupHierarchy
from maus.navigation import (
    AhbLocation,
    AhbLocationLayer,
    _AhbLocationDistance,
    _enhance_with_next_segment,
    _enhance_with_next_value_pool_entry,
    _find_common_ancestor_from_sgh,
    _is_opening_segment_line_border,
    _PseudoAhbLocation,
    calculate_distance,
    determine_hierarchy_changes,
    determine_locations,
    find_common_ancestor,
)

from .example_data_11042 import (  # type:ignore[import]
    example_flat_ahb_11042,
    example_sgh_11042,
    expected_changes_11042,
    expected_locations_11042,
)

sgh_utilmd_fv2204 = SegmentGroupHierarchy(
    segment_group=None,
    opening_segment="UNH",
    sub_hierarchy=[
        SegmentGroupHierarchy(segment_group="SG1", opening_segment="RFF", sub_hierarchy=[]),
        SegmentGroupHierarchy(
            segment_group="SG2",
            opening_segment="NAD",
            sub_hierarchy=[SegmentGroupHierarchy(segment_group="SG3", opening_segment="CTA", sub_hierarchy=[])],
        ),
        SegmentGroupHierarchy(
            segment_group="SG4",
            opening_segment="IDE",
            sub_hierarchy=[
                SegmentGroupHierarchy(
                    segment_group="SG5",
                    opening_segment="LOC",
                    sub_hierarchy=None,
                ),
                SegmentGroupHierarchy(segment_group="SG6", opening_segment="RFF", sub_hierarchy=None),
                SegmentGroupHierarchy(
                    segment_group="SG8",
                    opening_segment="SEQ",
                    sub_hierarchy=[
                        SegmentGroupHierarchy(segment_group="SG9", opening_segment="QTY", sub_hierarchy=None),
                        SegmentGroupHierarchy(segment_group="SG10", opening_segment="CCI", sub_hierarchy=None),
                    ],
                ),
                SegmentGroupHierarchy(segment_group="SG12", opening_segment="NAD", sub_hierarchy=None),
            ],
        ),
    ],
)


class TestNavigation:
    @pytest.mark.parametrize(
        "lines,expected",
        [
            pytest.param(
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code=None,
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry=None,
                        name="Das Eine",
                        guid=None,
                    ),
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
                [
                    (
                        AhbLine(
                            segment_group_key="SG4",
                            segment_code=None,
                            ahb_expression="X",
                            data_element="0333",
                            value_pool_entry=None,
                            name="Das Eine",
                            guid=None,
                        ),
                        "FOO",
                    ),
                    (
                        AhbLine(
                            segment_group_key="SG4",
                            segment_code="FOO",
                            ahb_expression="X",
                            data_element="0333",
                            value_pool_entry=None,
                            name="Das Eine",
                            guid=None,
                        ),
                        "FOO",
                    ),
                ],
            )
        ],
    )
    def test_enhance_line_with_next_segment(self, lines: List[AhbLine], expected: List[Tuple[AhbLine, str]]):
        actual = _enhance_with_next_segment(lines)
        assert actual == expected

    @pytest.mark.parametrize(
        "lines,expected",
        [
            pytest.param(
                [
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code=None,
                        ahb_expression="X",
                        data_element=None,
                        value_pool_entry=None,
                        name="Das Eine",
                        guid=None,
                    ),
                    AhbLine(
                        segment_group_key="SG4",
                        segment_code="FOO",
                        ahb_expression="X",
                        data_element="0333",
                        value_pool_entry="Z01",
                        name="Das Eine",
                        guid=None,
                    ),
                ],
                [
                    (
                        AhbLine(
                            segment_group_key="SG4",
                            segment_code=None,
                            ahb_expression="X",
                            data_element=None,
                            value_pool_entry=None,
                            name="Das Eine",
                            guid=None,
                        ),
                        "Z01",
                    ),
                    (
                        AhbLine(
                            segment_group_key="SG4",
                            segment_code="FOO",
                            ahb_expression="X",
                            data_element="0333",
                            value_pool_entry="Z01",
                            name="Das Eine",
                            guid=None,
                        ),
                        "Z01",
                    ),
                ],
            )
        ],
    )
    def test_enhance_line_with_next_value_pool_entry(self, lines: List[AhbLine], expected: List[Tuple[AhbLine, str]]):
        actual = _enhance_with_next_value_pool_entry(lines)
        assert actual == expected

    @pytest.mark.parametrize(
        "opening_segment,this_line,next_line,next_filled_segment,expected_result",
        [
            pytest.param(
                "CCI",
                AhbLine(
                    guid=UUID("b1538d12-9bf4-47a8-b34e-b9c012cc1000"),
                    segment_group_key="SG10",
                    segment_code="CCI",
                    data_element="7037",
                    value_pool_entry="Z07",
                    name="Verbrauch",
                    ahb_expression=None,
                    section_name="Lieferrichtung",
                ),
                AhbLine(
                    guid=UUID("505273ea-2287-49dd-abdc-56320026dde6"),
                    segment_group_key="SG10",
                    segment_code=None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression=None,
                    section_name="Zugeordnete Marktpartner",
                ),
                "CCI",
                True,
            ),
            pytest.param(
                "NAD",
                AhbLine(
                    guid=UUID("49538504-37f0-4b9b-b894-c3e8ecc64327"),
                    segment_group_key="SG12",
                    segment_code="RFF",
                    data_element="1154",
                    value_pool_entry=None,
                    name="ID der Marktlokation",
                    ahb_expression=None,
                    section_name="Referenz auf die ID der Marktlokation",
                ),
                AhbLine(
                    guid=UUID("57608e02-1eec-4e34-a77e-f6a9aa9026ff"),
                    segment_group_key="SG12",
                    segment_code=None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression=None,
                    section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                ),
                "NAD",
                True,
            ),
            pytest.param(
                "CCI",
                AhbLine(
                    guid=UUID("7cc3c40b-07d4-457a-a60f-1661485adcac"),
                    segment_group_key="SG10",
                    segment_code="CAV",
                    data_element="1131",
                    value_pool_entry="MP-ID",
                    name=None,
                    ahb_expression=None,
                    section_name="Lieferant",
                ),
                AhbLine(
                    guid=UUID("0e774e0c-7714-4853-82c8-742e65362eae"),
                    segment_group_key="SG10",
                    segment_code=None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression=None,
                    section_name="Übertragungsnetzbetreiber",
                ),
                "CAV",
                False,
            ),
        ],
    )
    def test_is_opening_segment_line_border(
        self,
        opening_segment: str,
        this_line: AhbLine,
        next_line: AhbLine,
        next_filled_segment: Optional[str],
        expected_result: bool,
    ):
        actual = _is_opening_segment_line_border(this_line, next_line, next_filled_segment, opening_segment)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "location_x, location_y, x_is_sub_of_y, y_is_parent_of_x",
        [
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD")
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD")
                    ]
                ),
                True,
                True,
                id="equality",
            ),
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD")
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE")
                    ]
                ),
                False,
                False,
                id="not equality",
            ),
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                    ]
                ),
                True,
                True,
                id="true sub",
            ),
        ],
    )
    def test_ahb_position_is_sub_or_parent_of(
        self, location_x: AhbLocation, location_y: AhbLocation, x_is_sub_of_y: bool, y_is_parent_of_x: bool
    ):
        assert location_x.is_sub_location_of(location_y) == x_is_sub_of_y
        assert location_y.is_parent_of(location_x) == y_is_parent_of_x

    @pytest.mark.parametrize(
        "location_x, location_y, expected",
        [
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                id="x == y",
            ),
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                    ]
                ),
                id="x is parent of y",
            ),
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="IOP"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                    ]
                ),
                id="x and y are siblings",
            ),
        ],
    )
    def test_find_common_ancestor(self, location_x: AhbLocation, location_y: AhbLocation, expected: AhbLocation):
        actual = find_common_ancestor(location_x, location_y)
        assert actual == expected

    @pytest.mark.parametrize(
        "sgh, sg_x, sg_y, expected",
        [
            pytest.param(
                sgh_utilmd_fv2204,
                "SG2",
                "SG2",
                _PseudoAhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key=None, opening_segment_code="UNH", opening_qualifier=None),
                        AhbLocationLayer(segment_group_key="SG2", opening_segment_code="NAD", opening_qualifier=None),
                    ]
                ),
                id="x and y are siblings (S2, UNH)",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                "SG12",
                "SG6",
                _PseudoAhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key=None, opening_segment_code="UNH", opening_qualifier=None),
                        AhbLocationLayer(segment_group_key="SG4", opening_segment_code="IDE", opening_qualifier=None),
                    ]
                ),
                id="x and y are siblings (S6.12)",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                "SG3",
                "SG12",
                _PseudoAhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key=None, opening_segment_code="UNH", opening_qualifier=None),
                    ]
                ),
                id="deep nested",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                "SG9",
                "SG6",
                _PseudoAhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key=None, opening_segment_code="UNH", opening_qualifier=None),
                        AhbLocationLayer(segment_group_key="SG4", opening_segment_code="IDE", opening_qualifier=None),
                    ]
                ),
                id="deep nested 2",
            ),
        ],
    )
    def test_find_common_ancestor_from_sgh(
        self, sg_x: str, sg_y: str, sgh: SegmentGroupHierarchy, expected: _PseudoAhbLocation
    ):
        actual = _find_common_ancestor_from_sgh(sg_x, sg_y, sgh)
        assert actual == expected

    @pytest.mark.parametrize(
        "location_x, location_y",
        [
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG7", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                id="there is no common root",
            ),
        ],
    )
    def test_find_no_common_ancestor(self, location_x: AhbLocation, location_y: AhbLocation):
        with pytest.raises(ValueError):
            _ = find_common_ancestor(location_x, location_y)

    @pytest.mark.parametrize(
        "location_x, location_y, expected",
        [
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                _AhbLocationDistance(layers_down=0, layers_up=0),
                id="x == y",
            ),
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                    ]
                ),
                _AhbLocationDistance(layers_down=0, layers_up=1),
                id="x is parent of y",
            ),
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="QWE"),
                    ]
                ),
                AhbLocation(
                    layers=[
                        AhbLocationLayer(segment_group_key="SG0", opening_segment_code="FOO", opening_qualifier="ASD"),
                        AhbLocationLayer(segment_group_key="SG1", opening_segment_code="BAR", opening_qualifier="IOP"),
                    ]
                ),
                _AhbLocationDistance(layers_down=1, layers_up=1),
                id="x and y are siblings",
            ),
        ],
    )
    def test_calculate_distance(self, location_x: AhbLocation, location_y: AhbLocation, expected: _AhbLocationDistance):
        actual = calculate_distance(location_x, location_y)
        assert actual == expected

    def _assert_consistency(self, locations: List[AhbLocation]) -> None:
        """
        assert that the locations are self-consistent in that regard, that the same segment group is always opened
        with the same segment code (which is derived from the SegmentGroupHierarchy)
        """
        sg_opening_segments: Dict[str, str] = {}  # maps SG-keys to their respective opening segments, e.g. "SG6":"RFF"
        for location in locations:
            for layer in location.layers:
                if layer.segment_group_key in sg_opening_segments:
                    if layer.segment_group_key is not None:
                        assert layer.opening_segment_code == sg_opening_segments[layer.segment_group_key]
                elif layer.segment_group_key is not None:
                    sg_opening_segments[layer.segment_group_key] = layer.opening_segment_code

    def test_determine_locations(self):
        actual_locations = [
            x[1] for x in determine_locations(example_sgh_11042, ahb_lines=example_flat_ahb_11042.lines)
        ]
        self._assert_consistency(actual_locations)
        assert actual_locations == expected_locations_11042

    def test_determine_differential_changes(self):
        actual_locations = [
            x[1] for x in determine_locations(example_sgh_11042, ahb_lines=example_flat_ahb_11042.lines)
        ]
        actual_changes = [x[1] for x in determine_hierarchy_changes(example_flat_ahb_11042.lines, example_sgh_11042)]
        location_and_changes = [
            (line, loc, change)
            for line, loc, change in zip(example_flat_ahb_11042.lines, actual_locations, actual_changes)
        ]
        assert location_and_changes is not None  # you may use this to update the 10k lines of equality assertions
        if actual_changes != expected_changes_11042:
            for n, (actual, expected) in enumerate(zip(actual_changes, expected_changes_11042, strict=True)):
                assert actual == expected, f"Error at line {n}: {example_flat_ahb_11042.lines[n]}"
        assert actual_changes == expected_changes_11042

    def test_remove_grouped_ahb_lines_containing_section_name(self):
        ahb_lines = [
            [
                AhbLine(
                    guid=UUID("b1538d12-9bf4-47a8-b34e-b9c012cc1000"),
                    segment_group_key="SG10",
                    segment_code="CCI",
                    data_element="7037",
                    value_pool_entry="Z07",
                    name="Verbrauch",
                    ahb_expression=None,
                    section_name="Lieferrichtung",
                ),
                AhbLine(
                    guid=UUID("505273ea-2287-49dd-abdc-56320026dde6"),
                    segment_group_key="SG10",
                    segment_code=None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression=None,
                    section_name="Abschnitts-Kontrollsegment",
                ),
            ],
            [
                AhbLine(
                    guid=UUID("b1538d12-9bf4-47a8-b34e-b9c012cc1000"),
                    segment_group_key="SG10",
                    segment_code="CCI",
                    data_element="7037",
                    value_pool_entry="Z07",
                    name="Verbrauch",
                    ahb_expression=None,
                    section_name="Lieferrichtung",
                )
            ],
        ]

        ahb_lines = _remove_grouped_ahb_lines_containing_section_name(ahb_lines, "Abschnitts-Kontrollsegment")

        assert len(ahb_lines) == 1
