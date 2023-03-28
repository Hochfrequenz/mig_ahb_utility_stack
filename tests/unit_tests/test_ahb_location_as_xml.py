from typing import List

import pytest  # type:ignore[import]

from maus.navigation import AhbLocation, AhbLocationLayer
from maus.reader.ahb_location_xml import from_xml_element, from_xml_elements, to_xml_element, to_xml_elements


class TestAhbLocationAsXml:
    """
    Tests the behaviour of the AhbLocation(Layer) can be serialized as XML
    """

    @pytest.mark.parametrize(
        "location",
        [
            pytest.param(
                AhbLocation(
                    layers=[
                        AhbLocationLayer(
                            segment_group_key=None, opening_segment_code="UNH", opening_qualifier="UTILMD"
                        ),
                        AhbLocationLayer(segment_group_key="SG2", opening_segment_code="NAD", opening_qualifier="MS"),
                        AhbLocationLayer(segment_group_key="SG3", opening_segment_code="CTA", opening_qualifier="IC"),
                    ],
                    segment_code="COM",
                    data_element_id="3148",
                    qualifier=None,
                )
            )
        ],
    )
    def test_xml_roundtrip(self, location: AhbLocation):
        xml_element = to_xml_element(location)
        deserialized_instance = from_xml_element(xml_element)
        assert location == deserialized_instance

    @pytest.mark.parametrize(
        "locations",
        [
            pytest.param(
                [
                    AhbLocation(
                        layers=[
                            AhbLocationLayer(
                                segment_group_key=None, opening_segment_code="UNH", opening_qualifier="UTILMD"
                            ),
                            AhbLocationLayer(
                                segment_group_key="SG2", opening_segment_code="NAD", opening_qualifier="MS"
                            ),
                            AhbLocationLayer(
                                segment_group_key="SG3", opening_segment_code="CTA", opening_qualifier="IC"
                            ),
                        ],
                        segment_code="COM",
                        data_element_id="3148",
                        qualifier=None,
                    ),
                    AhbLocation(
                        layers=[
                            AhbLocationLayer(
                                segment_group_key=None, opening_segment_code="UNH", opening_qualifier="UTILMD"
                            ),
                            AhbLocationLayer(
                                segment_group_key="SG2", opening_segment_code="NAD", opening_qualifier="MS"
                            ),
                            AhbLocationLayer(
                                segment_group_key="SG3", opening_segment_code="CTA", opening_qualifier="IC"
                            ),
                        ],
                        segment_code="CTA",
                        data_element_id=None,
                        qualifier=None,
                    ),
                ]
            )
        ],
    )
    def test_xml_roundtrip_list(self, locations: List[AhbLocation]):
        xml_elements = to_xml_elements(locations)
        deserialized_instances = from_xml_elements(xml_elements)
        assert locations == deserialized_instances
