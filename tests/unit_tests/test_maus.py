from typing import List, Optional, Tuple
from uuid import UUID

import pytest  # type:ignore[import]
from unit_tests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]

from maus import (
    _enhance_with_next_segment,
    _is_opening_segment_line_border,
    group_lines_by_segment_group,
    merge_lines_with_same_data_element,
    to_deep_ahb,
)
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
    def test_enhance_line_with_next_segemnt(self, lines: List[AhbLine], expected: List[Tuple[AhbLine, str]]):
        actual = _enhance_with_next_segment(lines)
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
                                        entered_input=None,
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
                                        entered_input=None,
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
                        guid=UUID("3d998c69-676e-4550-a294-911cc33be232"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Kunde des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("14607029-22f4-4ed7-8ae0-f902f9096308"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Kunde des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("627032bf-cf03-4045-a20c-1933b011a6ab"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="Z09",
                        name="Kunde des LF",
                        ahb_expression=None,
                        section_name="Kunde des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("15ef1f0f-379d-4455-9bed-00336933de53"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3036",
                        value_pool_entry=None,
                        name="Name",
                        ahb_expression=None,
                        section_name="Kunde des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("6a303c15-be14-44b9-8697-a17ee30fa64a"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z01",
                        name="Struktur von Personennamen",
                        ahb_expression=None,
                        section_name="Kunde des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("d3f8ec05-0658-42a8-ac75-4c3234bbf1b7"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z02",
                        name="Struktur der Firmenbezeichnung",
                        ahb_expression=None,
                        section_name="Kunde des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("035a4641-724f-4b30-befe-11acc5683516"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("a123d651-b7e7-44e4-9c92-d851a06aac39"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("8e0e6f72-52e4-4404-86ad-ddc00ff0a445"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1153",
                        value_pool_entry="Z18",
                        name="Marktlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
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
                    AhbLine(
                        guid=UUID("ffdb04c1-2659-4a06-be21-8bca4e869d3a"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("91024719-1dd3-4048-b944-4409327b231b"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="Z04",
                        name="Korrespondenzanschriftdes Kunden des LF",
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("2b6cc787-a995-4525-a136-abc8aa65fde1"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3036",
                        value_pool_entry=None,
                        name="Name",
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("e61d216a-f646-439d-8ca8-88721909fc38"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z01",
                        name="Struktur von Personennamen",
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("95e4a157-94a1-46e4-89f6-0bad46ae5905"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z02",
                        name="Struktur der Firmenbezeichnung",
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("d3b3b633-3f0f-4fc0-8d42-e1f425814f03"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3042",
                        value_pool_entry=None,
                        name="Straße und Hausnummer oderPostfach",
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("c657b1c3-2b39-452d-86e4-42ad16e3875d"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3164",
                        value_pool_entry=None,
                        name="Ort",
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("2bc5cc99-49a2-47e9-b4a9-c729f346bbb8"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3251",
                        value_pool_entry=None,
                        name="Postleitzahl",
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("80b30a95-cebd-4cab-97ce-270d1b5d07c5"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3207",
                        value_pool_entry=None,
                        name="Ländername, Code",
                        ahb_expression=None,
                        section_name="Korrespondenzanschrift des Kunden des Lieferanten",
                    ),
                    AhbLine(
                        guid=UUID("830758e8-a494-4030-a57f-bd312566ef09"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("de844ce5-1700-4878-bdd1-fdb3b47fe388"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("8d5b9bb9-44a9-4246-b357-46fbbcba7875"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1153",
                        value_pool_entry="Z18",
                        name="Marktlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("337db3df-4213-491b-be57-c9f305466713"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1154",
                        value_pool_entry=None,
                        name="ID der Marktlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("413e1fe8-9e67-4384-895e-c65c2f8e27a2"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Muss",
                        section_name="Kunde des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("bd3069da-4e3e-4029-a1c9-5e768b906329"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Muss",
                        section_name="Kunde des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("315621e3-3496-41f7-af45-c94da66fb22c"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="Z07",
                        name="Kunde des MSB",
                        ahb_expression="X",
                        section_name="Kunde des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("3cc5a59a-7d73-44f4-9f09-1c4632666c14"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3036",
                        value_pool_entry=None,
                        name="Name",
                        ahb_expression="X",
                        section_name="Kunde des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("695de358-076e-4284-8e4b-b1d57dab85fd"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z01",
                        name="Struktur von Personennamen",
                        ahb_expression="X",
                        section_name="Kunde des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("b26bd4fb-0147-493c-8fc2-ace2df0c5970"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z02",
                        name="Struktur der Firmenbezeichnung",
                        ahb_expression="X",
                        section_name="Kunde des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("e3d674c9-8514-498d-87f0-09753c1b8e90"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("11e870ec-560c-4531-8bf8-d60735a23de9"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("777fa652-1398-4d93-9c05-8bb668e6af2e"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1153",
                        value_pool_entry="Z19",
                        name="Messlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("be4a10a5-c775-4d1b-982c-7b6e13075a3d"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1154",
                        value_pool_entry=None,
                        name="ID der Messlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("d969afe7-0ee8-4854-88cc-3417cd1ba6c2"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Muss",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("e0ddd585-4daa-4996-b968-f7c9a92ed050"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Muss",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("e1b62fae-ead5-4aa8-bc3e-c4362a3b7362"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="Z08",
                        name="Korrespondenzanschriftdes Kunden des MSB",
                        ahb_expression="X",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("6a88bdfa-1481-4956-b30a-ed7a00c7822c"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3036",
                        value_pool_entry=None,
                        name="Name",
                        ahb_expression="X",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("ea455817-011e-4662-b298-44e76ac5f814"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z01",
                        name="Struktur von Personennamen",
                        ahb_expression="X",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("d419700b-fe4f-443f-b544-51925a9f5893"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z02",
                        name="Struktur der Firmenbezeichnung",
                        ahb_expression="X",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("21c8b41c-28f2-48ac-8523-360354d58b6f"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3042",
                        value_pool_entry=None,
                        name="Straße und Hausnummer oderPostfach",
                        ahb_expression="X",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("70c11c78-a890-4118-a509-1fa50a829fed"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3164",
                        value_pool_entry=None,
                        name="Ort",
                        ahb_expression="X",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("67357d06-5184-4e80-b9ed-07a101c56e8c"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3251",
                        value_pool_entry=None,
                        name="Postleitzahl",
                        ahb_expression="M [268]S [166]",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("bd323f9f-232f-47b3-9582-8954a419c6c0"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3207",
                        value_pool_entry=None,
                        name="Ländername, Code",
                        ahb_expression="X",
                        section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                    ),
                    AhbLine(
                        guid=UUID("7c5fd79f-545f-40cf-a283-9ff057693b0b"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("b48fe9ce-e69a-4ecd-ba2a-0b6133afe2a6"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("bd04bc15-f860-4033-bfc2-cdd996a76976"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1153",
                        value_pool_entry="Z18",
                        name="Marktlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("e4e0838c-789c-4406-b68e-30155d4fc711"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1154",
                        value_pool_entry=None,
                        name="ID der Marktlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("c6ebb640-f3a9-41ea-96f0-dc672a73744a"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Soll [165]",
                        section_name="Messlokationsadresse",
                    ),
                    AhbLine(
                        guid=UUID("4a378d8d-241b-4660-b1a5-212f014d3ed8"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Muss",
                        section_name="Messlokationsadresse",
                    ),
                    AhbLine(
                        guid=UUID("eada0044-22a0-4b64-a107-d36a93050612"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="Z03",
                        name="Messlokationsadresse",
                        ahb_expression="X",
                        section_name="Messlokationsadresse",
                    ),
                    AhbLine(
                        guid=UUID("65b587ba-fda5-439c-b60e-1bf6eabc1dd8"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3124",
                        value_pool_entry=None,
                        name="Zusatzinformation zurIdentifizierung",
                        ahb_expression="K",
                        section_name="Messlokationsadresse",
                    ),
                    AhbLine(
                        guid=UUID("25bf79f4-afb3-444b-8f63-feeaf59bc258"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3042",
                        value_pool_entry=None,
                        name="Straße und Hausnummer oderPostfach",
                        ahb_expression="S [166]M [212]",
                        section_name="Messlokationsadresse",
                    ),
                    AhbLine(
                        guid=UUID("adf2eb59-306a-47c2-811e-f6f9a2d7afec"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3164",
                        value_pool_entry=None,
                        name="Ort",
                        ahb_expression="X",
                        section_name="Messlokationsadresse",
                    ),
                    AhbLine(
                        guid=UUID("b91bfdae-12ff-4cda-99e3-fdbce6a6fa53"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3251",
                        value_pool_entry=None,
                        name="Postleitzahl",
                        ahb_expression="X",
                        section_name="Messlokationsadresse",
                    ),
                    AhbLine(
                        guid=UUID("7f881ae5-9f6d-40e9-b3b4-beb2a91a5fa4"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3207",
                        value_pool_entry=None,
                        name="Ländername, Code",
                        ahb_expression="X",
                        section_name="Messlokationsadresse",
                    ),
                    AhbLine(
                        guid=UUID("7334e036-505c-4bf8-ab7c-2df58fb77e33"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID einer Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("16866b1c-52ff-4be1-b471-fe19486875db"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID einer Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("918056f0-4aa2-4a22-abd7-31ef9760f7e3"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1153",
                        value_pool_entry="Z19",
                        name="Messlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID einer Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("f7def4a4-12ec-4f24-86be-42f5384771a7"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1154",
                        value_pool_entry=None,
                        name="ID einer Messlokation",
                        ahb_expression=None,
                        section_name="Referenz auf die ID einer Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("6fbf381b-47b5-4e38-b205-ee1b7d5eb97d"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Muss",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("aeadee34-efd9-4157-809b-c72416503001"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Muss",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("a2c8a4ce-f9cc-4c64-a2ee-76b559c9ad35"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3035",
                        value_pool_entry="Z05",
                        name="Name und Adresse fürdie Ablesekarte",
                        ahb_expression="X",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("20dbb001-7f69-404a-9837-4309b217f948"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3036",
                        value_pool_entry=None,
                        name="Name",
                        ahb_expression="X",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("2f137ec0-ffca-440b-801d-aeadf2a6acb0"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z01",
                        name="Struktur von Personennamen",
                        ahb_expression="X",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("13f24503-3aea-416d-bca4-2dd6a8ced10f"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3045",
                        value_pool_entry="Z02",
                        name="Struktur der Firmenbezeichnung",
                        ahb_expression="X",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("33bb5866-c2a2-4ca6-bb9a-1734aceacfed"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3042",
                        value_pool_entry=None,
                        name="Straße und Hausnummer oderPostfach",
                        ahb_expression="X",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("33494dd6-de05-48a9-b7f9-588b711b3702"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3164",
                        value_pool_entry=None,
                        name="Ort",
                        ahb_expression="X",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("8f467ccb-67db-4c84-9626-695869e09427"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3251",
                        value_pool_entry=None,
                        name="Postleitzahl",
                        ahb_expression="M [268]S [166]",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("e0af702f-a5e9-42c9-8177-d82dd9b028ee"),
                        segment_group_key="SG12",
                        segment_code="NAD",
                        data_element="3207",
                        value_pool_entry=None,
                        name="Ländername, Code",
                        ahb_expression="X",
                        section_name="Name und Adresse für die Ablesekarte",
                    ),
                    AhbLine(
                        guid=UUID("eb861073-10ee-44d8-bc1c-ab668f19a857"),
                        segment_group_key="SG12",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Referenz auf die ID einer Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("50179d8a-6fd3-4814-9158-7ef132782ab7"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression="Kann",
                        section_name="Referenz auf die ID einer Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("f7e7c1cb-8de5-46db-929d-6aa8cc3fb028"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1153",
                        value_pool_entry="Z19",
                        name="Messlokation",
                        ahb_expression="X",
                        section_name="Referenz auf die ID einer Messlokation",
                    ),
                    AhbLine(
                        guid=UUID("dd410733-892d-433e-91fd-893b5b3fc782"),
                        segment_group_key="SG12",
                        segment_code="RFF",
                        data_element="1154",
                        value_pool_entry=None,
                        name="ID einer Messlokation",
                        ahb_expression="X [951]",
                        section_name="Referenz auf die ID einer Messlokation",
                    ),
                ],
                SegmentGroupHierarchy(segment_group="SG12", sub_hierarchy=None, opening_segment="NAD"),
                [
                    SegmentGroup(
                        discriminator="SG12",
                        ahb_expression="Muss",
                        segments=[
                            Segment(
                                discriminator="NAD",
                                ahb_expression="Muss",
                                data_elements=[
                                    DataElementValuePool(
                                        discriminator="SG12->NAD->3035",
                                        data_element_id="3035",
                                        entered_input=None,
                                        value_pool=[
                                            ValuePoolEntry(qualifier="Z07", meaning="Kunde des MSB", ahb_expression="X")
                                        ],
                                    ),
                                    DataElementFreeText(
                                        discriminator="Name",
                                        data_element_id="3036",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementValuePool(
                                        discriminator="SG12->NAD->3045",
                                        data_element_id="3045",
                                        entered_input=None,
                                        value_pool=[
                                            ValuePoolEntry(
                                                qualifier="Z01",
                                                meaning="Struktur von Personennamen",
                                                ahb_expression="X",
                                            ),
                                            ValuePoolEntry(
                                                qualifier="Z02",
                                                meaning="Struktur der Firmenbezeichnung",
                                                ahb_expression="X",
                                            ),
                                        ],
                                    ),
                                ],
                                section_name="Kunde des Messstellenbetreibers",
                            )
                        ],
                        segment_groups=[],
                    ),
                    SegmentGroup(
                        discriminator="SG12",
                        ahb_expression="Muss",
                        segments=[
                            Segment(
                                discriminator="NAD",
                                ahb_expression="Muss",
                                data_elements=[
                                    DataElementValuePool(
                                        discriminator="SG12->NAD->3035",
                                        data_element_id="3035",
                                        entered_input=None,
                                        value_pool=[
                                            ValuePoolEntry(
                                                qualifier="Z08",
                                                meaning="Korrespondenzanschriftdes Kunden des MSB",
                                                ahb_expression="X",
                                            )
                                        ],
                                    ),
                                    DataElementFreeText(
                                        discriminator="Name",
                                        data_element_id="3036",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementValuePool(
                                        discriminator="SG12->NAD->3045",
                                        data_element_id="3045",
                                        entered_input=None,
                                        value_pool=[
                                            ValuePoolEntry(
                                                qualifier="Z01",
                                                meaning="Struktur von Personennamen",
                                                ahb_expression="X",
                                            ),
                                            ValuePoolEntry(
                                                qualifier="Z02",
                                                meaning="Struktur der Firmenbezeichnung",
                                                ahb_expression="X",
                                            ),
                                        ],
                                    ),
                                    DataElementFreeText(
                                        discriminator="Straße und Hausnummer oderPostfach",
                                        data_element_id="3042",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Ort",
                                        data_element_id="3164",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Postleitzahl",
                                        data_element_id="3251",
                                        entered_input=None,
                                        ahb_expression="M [268]S [166]",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Ländername, Code",
                                        data_element_id="3207",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                ],
                                section_name="Korrespondenzanschrift des Kunden des Messstellenbetreibers",
                            )
                        ],
                        segment_groups=[],
                    ),
                    SegmentGroup(
                        discriminator="SG12",
                        ahb_expression="Soll [165]",
                        segments=[
                            Segment(
                                discriminator="NAD",
                                ahb_expression="Muss",
                                data_elements=[
                                    DataElementValuePool(
                                        discriminator="SG12->NAD->3035",
                                        data_element_id="3035",
                                        entered_input=None,
                                        value_pool=[
                                            ValuePoolEntry(
                                                qualifier="Z03", meaning="Messlokationsadresse", ahb_expression="X"
                                            )
                                        ],
                                    ),
                                    DataElementFreeText(
                                        discriminator="Zusatzinformation zurIdentifizierung",
                                        data_element_id="3124",
                                        entered_input=None,
                                        ahb_expression="K",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Straße und Hausnummer oderPostfach",
                                        data_element_id="3042",
                                        entered_input=None,
                                        ahb_expression="S [166]M [212]",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Ort",
                                        data_element_id="3164",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Postleitzahl",
                                        data_element_id="3251",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Ländername, Code",
                                        data_element_id="3207",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                ],
                                section_name="Messlokationsadresse",
                            )
                        ],
                        segment_groups=[],
                    ),
                    SegmentGroup(
                        discriminator="SG12",
                        ahb_expression="Muss",
                        segments=[
                            Segment(
                                discriminator="NAD",
                                ahb_expression="Muss",
                                data_elements=[
                                    DataElementValuePool(
                                        discriminator="SG12->NAD->3035",
                                        data_element_id="3035",
                                        entered_input=None,
                                        value_pool=[
                                            ValuePoolEntry(
                                                qualifier="Z05",
                                                meaning="Name und Adresse fürdie Ablesekarte",
                                                ahb_expression="X",
                                            )
                                        ],
                                    ),
                                    DataElementFreeText(
                                        discriminator="Name",
                                        data_element_id="3036",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementValuePool(
                                        discriminator="SG12->NAD->3045",
                                        data_element_id="3045",
                                        entered_input=None,
                                        value_pool=[
                                            ValuePoolEntry(
                                                qualifier="Z01",
                                                meaning="Struktur von Personennamen",
                                                ahb_expression="X",
                                            ),
                                            ValuePoolEntry(
                                                qualifier="Z02",
                                                meaning="Struktur der Firmenbezeichnung",
                                                ahb_expression="X",
                                            ),
                                        ],
                                    ),
                                    DataElementFreeText(
                                        discriminator="Straße und Hausnummer oderPostfach",
                                        data_element_id="3042",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Ort",
                                        data_element_id="3164",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Postleitzahl",
                                        data_element_id="3251",
                                        entered_input=None,
                                        ahb_expression="M [268]S [166]",
                                    ),
                                    DataElementFreeText(
                                        discriminator="Ländername, Code",
                                        data_element_id="3207",
                                        entered_input=None,
                                        ahb_expression="X",
                                    ),
                                ],
                                section_name="Name und Adresse für die Ablesekarte",
                            ),
                            Segment(
                                discriminator="RFF",
                                ahb_expression="Kann",
                                data_elements=[
                                    DataElementValuePool(
                                        discriminator="SG12->RFF->1153",
                                        data_element_id="1153",
                                        entered_input=None,
                                        value_pool=[
                                            ValuePoolEntry(qualifier="Z19", meaning="Messlokation", ahb_expression="X")
                                        ],
                                    ),
                                    DataElementFreeText(
                                        discriminator="ID einer Messlokation",
                                        data_element_id="1154",
                                        entered_input=None,
                                        ahb_expression="X [951]",
                                    ),
                                ],
                                section_name="Referenz auf die ID einer Messlokation",
                            ),
                        ],
                        segment_groups=[],
                    ),
                ],
                id="multiple SG12, first one not mandatory (like in 11042)",
            ),
            pytest.param(
                [
                    AhbLine(
                        guid=UUID("b88c8c5a-6e02-4dfc-869b-6be57ba80c15"),
                        segment_group_key="SG10",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Lieferrichtung",
                    ),
                    AhbLine(
                        guid=UUID("77fea6b4-ae5d-44ae-b09c-62810f957ff0"),
                        segment_group_key="SG10",
                        segment_code="CCI",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Lieferrichtung",
                    ),
                    AhbLine(
                        guid=UUID("55f3878a-bb72-4a42-99bb-282eef6039a3"),
                        segment_group_key="SG10",
                        segment_code="CCI",
                        data_element="7059",
                        value_pool_entry="Z30",
                        name="Lieferrichtung",
                        ahb_expression=None,
                        section_name="Lieferrichtung",
                    ),
                    AhbLine(
                        guid=UUID("8fb16461-5c38-4b8b-bf1b-87dcf148e426"),
                        segment_group_key="SG10",
                        segment_code="CCI",
                        data_element="7037",
                        value_pool_entry="Z06",
                        name="Erzeugung",
                        ahb_expression=None,
                        section_name="Lieferrichtung",
                    ),
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
                    AhbLine(
                        guid=UUID("f5388ff1-9b79-4f74-a840-1545c623b478"),
                        segment_group_key="SG10",
                        segment_code="CCI",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Zugeordnete Marktpartner",
                    ),
                    AhbLine(
                        guid=UUID("547f89a3-e856-4258-99ca-d99127674680"),
                        segment_group_key="SG10",
                        segment_code="CCI",
                        data_element="7037",
                        value_pool_entry="ZB3",
                        name="ZugeordneterMarktpartner",
                        ahb_expression=None,
                        section_name="Zugeordnete Marktpartner",
                    ),
                    AhbLine(
                        guid=UUID("f32b860c-7a4d-406f-b776-bcad59f13742"),
                        segment_group_key="SG10",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Lieferant",
                    ),
                    AhbLine(
                        guid=UUID("95817b5f-51c4-4fde-be78-0200e070f6b1"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Lieferant",
                    ),
                    AhbLine(
                        guid=UUID("c7eef5bd-dd05-40cc-b25c-752ea9a18bf2"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7111",
                        value_pool_entry="Z89",
                        name="LF",
                        ahb_expression=None,
                        section_name="Lieferant",
                    ),
                    AhbLine(
                        guid=UUID("39c31c84-731b-420a-aeb3-a8686da800df"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="1131",
                        value_pool_entry="MP-ID",
                        name=None,
                        ahb_expression=None,
                        section_name="Lieferant",
                    ),
                    AhbLine(
                        guid=UUID("16b68c26-ff51-4d5c-ae2f-1b71fda8bf44"),
                        segment_group_key="SG10",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Übertragungsnetzbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("9926e539-e764-4b50-a6f4-82ddb6738a1a"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Übertragungsnetzbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("b19ac3e5-97a7-4453-859e-c8b018682b6e"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7111",
                        value_pool_entry="Z90",
                        name="ÜNB",
                        ahb_expression=None,
                        section_name="Übertragungsnetzbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("9fed91e6-5a14-4ea7-8775-b85b79478282"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="1131",
                        value_pool_entry="MP-ID",
                        name=None,
                        ahb_expression=None,
                        section_name="Übertragungsnetzbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("311be788-a3cd-4b3e-a6fe-1955b17fc880"),
                        segment_group_key="SG10",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Messstellenbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("d4e700f6-4080-4f30-a8be-a705c618354a"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Messstellenbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("ef42e9e5-1c8c-476d-90ac-0b76cb53e9c2"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7111",
                        value_pool_entry="Z91",
                        name="MSB",
                        ahb_expression=None,
                        section_name="Messstellenbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("9186fd71-31b9-4069-921d-62e66748e10b"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="1131",
                        value_pool_entry="MP-ID",
                        name=None,
                        ahb_expression=None,
                        section_name="Messstellenbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("ae2c1fab-e2e0-47ea-8d99-675cde9985b3"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7110",
                        value_pool_entry="Z19",
                        name="Auf vertraglicher Grundlage gegenüber Anschlussnutzer / Anschlussnehmer",
                        ahb_expression=None,
                        section_name="Messstellenbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("f24c33a7-262f-4797-b0a6-e25193205cf4"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7110",
                        value_pool_entry="Z20",
                        name="In der Ausübung der",
                        ahb_expression=None,
                        section_name="Messstellenbetreiber",
                    ),
                    AhbLine(
                        guid=UUID("c655d127-2ab5-476a-8e8b-bbb6152eab54"),
                        segment_group_key="SG10",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("24624cf0-0704-4c58-b9d2-d7db380ed1bb"),
                        segment_group_key="SG10",
                        segment_code="CCI",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("62dd2c75-746d-4026-ad6f-50df0046513a"),
                        segment_group_key="SG10",
                        segment_code="CCI",
                        data_element="7037",
                        value_pool_entry="E03",
                        name="Spannungsebene derMarktlokation",
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("41071cd6-8a9f-499e-befd-4ace26320e57"),
                        segment_group_key="SG10",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("b7d75304-ac7d-47bf-9003-cce9f6e309e7"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("85c3b018-4400-4917-9a21-71a84d35cf8c"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7111",
                        value_pool_entry="E03",
                        name="Höchstspannung",
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("5e5ff3df-3977-4e2f-a395-7b59e8f3b550"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7111",
                        value_pool_entry="E04",
                        name="Hochspannung",
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("2e77b4f0-5a05-4421-9192-9cda63a240f9"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7111",
                        value_pool_entry="E05",
                        name="Mittelspannung",
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                    AhbLine(
                        guid=UUID("9a7b5a81-0328-4d7d-88f0-b2a218660fbc"),
                        segment_group_key="SG10",
                        segment_code="CAV",
                        data_element="7111",
                        value_pool_entry="E06",
                        name="Niederspannung",
                        ahb_expression=None,
                        section_name="Spannungsebene der Marktlokation",
                    ),
                ],
                SegmentGroupHierarchy(segment_group="SG10", sub_hierarchy=None, opening_segment="CCI"),
                [],
                id="UTILMD SG10",
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
                                                    entered_input=None,
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
