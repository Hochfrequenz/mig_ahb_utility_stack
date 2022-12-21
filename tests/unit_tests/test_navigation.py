from typing import List, Optional, Tuple
from uuid import UUID

import pytest  # type:ignore[import]
from jsonpath_ng.ext import parse  # type:ignore[import] #  jsonpath is just installed in the tests
from more_itertools import last

from maus import SegmentGroupHierarchy
from maus.models.anwendungshandbuch import AhbLine
from maus.navigation import (
    AhbLocation,
    AhbLocationLayer,
    _AhbLocationDistance,
    _enhance_with_next_segment,
    _enhance_with_next_value_pool_entry,
    _is_opening_segment_line_border,
    calculate_distance,
    determine_locations,
    find_common_ancestor,
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
        "sgh,lines,expected_location",
        [
            pytest.param(
                sgh_utilmd_fv2204,
                [
                    AhbLine(
                        guid=UUID("0e774e0c-7714-4853-82c8-742e65362eae"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0062",
                        value_pool_entry=None,
                        name="Nachrichtenreferenznummer",
                        section_name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("21a6dacb-479f-48f7-9cda-41a01f0d6f0a"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0065",
                        value_pool_entry="UTILMD",
                        name=None,
                        section_name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                ],
                AhbLocation(
                    layers=[
                        AhbLocationLayer(opening_qualifier="UTILMD", segment_group_key=None, opening_segment_code="UNH")
                    ],
                    data_element_id="0065",
                ),
                id="first segment on root level = stay",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                [
                    AhbLine(
                        guid=UUID("0e774e0c-7714-4853-82c8-742e65362eae"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0062",
                        value_pool_entry=None,
                        name="Nachrichtenreferenznummer",
                        section_name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("21a6dacb-479f-48f7-9cda-41a01f0d6f0a"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0065",
                        value_pool_entry="UTILMD",
                        name=None,
                        section_name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("807efb26-5003-4ba0-b98a-602f9eb1f7e5"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0052",
                        value_pool_entry="D",
                        name="Entwurfsversion",
                        section_name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                ],
                AhbLocation(
                    layers=[
                        AhbLocationLayer(opening_qualifier="UTILMD", segment_group_key=None, opening_segment_code="UNH")
                    ],
                    data_element_id="0052",
                ),
                id="first segment on root level = stay don't move to non-existent neighbour",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                [
                    AhbLine(
                        guid=UUID("98f29214-5ec2-4635-8fcd-67e26804c2fe"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0065",
                        value_pool_entry="UTILMD",
                        section_name="Netzanschluss-Stammdaten",
                        name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("f621ef9e-64a5-4c6a-ba8c-9b71db214e84"),
                        segment_group_key="SG2",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="MS",
                        section_name="MP-ID Absender",
                        name="Nachrichtenaussteller bzw. -absender",
                        ahb_expression="X",
                    ),
                ],
                AhbLocation(
                    layers=[
                        AhbLocationLayer(
                            segment_group_key=None, opening_segment_code="UNH", opening_qualifier="UTILMD"
                        ),
                        AhbLocationLayer(segment_group_key="SG2", opening_segment_code="NAD", opening_qualifier="MS"),
                    ],
                    data_element_id="3035",
                ),
                id="switch from UNH into SG2",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                [
                    AhbLine(
                        guid=UUID("98f29214-5ec2-4635-8fcd-67e26804c2fe"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0065",
                        value_pool_entry="UTILMD",
                        section_name="Netzanschluss-Stammdaten",
                        name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("f621ef9e-64a5-4c6a-ba8c-9b71db214e84"),
                        segment_group_key="SG2",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="MS",
                        section_name="MP-ID Absender",
                        name="Nachrichtenaussteller bzw. -absender",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("ad9eb5e0-2cd8-42af-9135-ef2dfa94d2fa"),
                        segment_group_key="SG3",
                        segment_code="CTA",
                        data_element="3139",
                        value_pool_entry="IC",
                        section_name="Ansprechpartner",
                        name="Informationskontakt",
                        ahb_expression="X",
                    ),
                ],
                AhbLocation(
                    layers=[
                        AhbLocationLayer(
                            segment_group_key=None, opening_segment_code="UNH", opening_qualifier="UTILMD"
                        ),
                        AhbLocationLayer(segment_group_key="SG2", opening_segment_code="NAD", opening_qualifier="MS"),
                        AhbLocationLayer(segment_group_key="SG3", opening_segment_code="CTA", opening_qualifier="IC"),
                    ],
                    data_element_id="3139",
                ),
                id="UNH to SG2 to SG3",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                [
                    AhbLine(
                        guid=UUID("98f29214-5ec2-4635-8fcd-67e26804c2fe"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0065",
                        value_pool_entry="UTILMD",
                        section_name="Netzanschluss-Stammdaten",
                        name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("f621ef9e-64a5-4c6a-ba8c-9b71db214e84"),
                        segment_group_key="SG2",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="MS",
                        section_name="MP-ID Absender",
                        name="Nachrichtenaussteller bzw. -absender",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("ad9eb5e0-2cd8-42af-9135-ef2dfa94d2fa"),
                        segment_group_key="SG3",
                        segment_code="CTA",
                        data_element="3139",
                        value_pool_entry="IC",
                        section_name="Ansprechpartner",
                        name="Informationskontakt",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("895d49d9-de4d-4af8-9180-06cb6719b537"),
                        segment_group_key="SG2",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="MR",
                        section_name="MP-ID Empfänger",
                        name="Nachrichtenaussteller bzw. -absender",
                        ahb_expression="X",
                    ),
                ],
                AhbLocation(
                    layers=[
                        AhbLocationLayer(
                            segment_group_key=None, opening_segment_code="UNH", opening_qualifier="UTILMD"
                        ),
                        # we entered the SG2 NAD+MS and SG3 CTA+IC, then left them again, that's why they are not part
                        # of this location anymore although we iterated over them.
                        AhbLocationLayer(segment_group_key="SG2", opening_segment_code="NAD", opening_qualifier="MR"),
                    ],
                    data_element_id="3035",
                ),
                id="UNH to SG2 NAD MS to SG3 back to next SG2 NAD MR",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                [
                    AhbLine(
                        guid=UUID("98f29214-5ec2-4635-8fcd-67e26804c2fe"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0065",
                        value_pool_entry="UTILMD",
                        section_name="Netzanschluss-Stammdaten",
                        name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("f621ef9e-64a5-4c6a-ba8c-9b71db214e84"),
                        segment_group_key="SG2",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="MS",
                        section_name="MP-ID Absender",
                        name="Nachrichtenaussteller bzw. -absender",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("ad9eb5e0-2cd8-42af-9135-ef2dfa94d2fa"),
                        segment_group_key="SG3",
                        segment_code="CTA",
                        data_element="3139",
                        value_pool_entry="IC",
                        section_name="Ansprechpartner",
                        name="Informationskontakt",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("895d49d9-de4d-4af8-9180-06cb6719b537"),
                        segment_group_key="SG2",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="MR",
                        section_name="MP-ID Empfänger",
                        name="Nachrichtenaussteller bzw. -absender",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("f74151b7-071a-48ce-9d8c-3bf66497d9ca"),
                        segment_group_key="SG4",
                        segment_code="IDE",
                        data_element="7495",
                        value_pool_entry="24",
                        section_name="Vorgang",
                        name="Transaktion",
                        ahb_expression="X",
                    ),
                ],
                AhbLocation(
                    layers=[
                        AhbLocationLayer(
                            segment_group_key=None, opening_segment_code="UNH", opening_qualifier="UTILMD"
                        ),
                        AhbLocationLayer(segment_group_key="SG4", opening_segment_code="IDE", opening_qualifier="24"),
                    ],
                    data_element_id="7495",
                ),
                id="UNH to SG4",
            ),
            pytest.param(
                sgh_utilmd_fv2204,
                [
                    AhbLine(
                        guid=UUID("98f29214-5ec2-4635-8fcd-67e26804c2fe"),
                        segment_group_key=None,
                        segment_code="UNH",
                        data_element="0065",
                        value_pool_entry="UTILMD",
                        section_name="Netzanschluss-Stammdaten",
                        name="Nachrichten-Kopfsegment",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("f621ef9e-64a5-4c6a-ba8c-9b71db214e84"),
                        segment_group_key="SG2",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="MS",
                        section_name="MP-ID Absender",
                        name="Nachrichtenaussteller bzw. -absender",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("ad9eb5e0-2cd8-42af-9135-ef2dfa94d2fa"),
                        segment_group_key="SG3",
                        segment_code="CTA",
                        data_element="3139",
                        value_pool_entry="IC",
                        section_name="Ansprechpartner",
                        name="Informationskontakt",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("895d49d9-de4d-4af8-9180-06cb6719b537"),
                        segment_group_key="SG2",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="MR",
                        section_name="MP-ID Empfänger",
                        name="Nachrichtenaussteller bzw. -absender",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("f74151b7-071a-48ce-9d8c-3bf66497d9ca"),
                        segment_group_key="SG4",
                        segment_code="IDE",
                        data_element="7495",
                        value_pool_entry="24",
                        section_name="Vorgang",
                        name="Transaktion",
                        ahb_expression="X",
                    ),
                    AhbLine(
                        guid=UUID("f74151b7-071a-48ce-9d8c-3bf66497d9ca"),
                        segment_group_key="SG5",
                        segment_code="LOC",
                        data_element="3227",
                        value_pool_entry="172",
                        section_name="Meldepunkt",
                        name="Meldepunkt",
                        ahb_expression="X",
                    ),
                ],
                AhbLocation(
                    layers=[
                        AhbLocationLayer(
                            segment_group_key=None, opening_segment_code="UNH", opening_qualifier="UTILMD"
                        ),
                        AhbLocationLayer(segment_group_key="SG4", opening_segment_code="IDE", opening_qualifier="24"),
                        AhbLocationLayer(segment_group_key="SG5", opening_segment_code="LOC", opening_qualifier="172"),
                    ],
                    data_element_id="3227",
                ),
                id="UNH to SG5",
            ),
        ],
    )
    def test_determine_location(self, sgh: SegmentGroupHierarchy, lines: List[AhbLine], expected_location: AhbLocation):
        """
        The test setup gives a segment group hierarchy and some ahb lines.
        The test then iterates over the given lines. And asserts that the results returned are as expected, one by one
        """
        actual_locations = [x[1] for x in determine_locations(sgh, ahb_lines=lines)]
        assert len(actual_locations) == len(lines)
        actual = last(actual_locations)
        assert actual == expected_location

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
