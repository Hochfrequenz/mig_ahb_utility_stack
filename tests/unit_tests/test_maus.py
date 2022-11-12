from typing import List
from uuid import UUID

import pytest  # type:ignore[import]
from unit_tests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]

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
