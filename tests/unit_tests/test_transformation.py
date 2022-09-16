from typing import Dict, Optional

import pytest  # type:ignore[import]
from jsonpath_ng.ext import parse  # jsonpath is just installed in the tests

from maus.models.edifact_components import DataElementValuePool, ValuePoolEntry
from maus.transformation import generate_value_pool_replacement


class TestTransformation:
    def test_find_equivalent_after_transformation(self):
        non_edifact_representation = {
            "a key": [{"an entry": "NON_EDIFACT_Z09"}],
            "another key": [{}, {}, {"another entry": "NON_EDIFACT_E01"}],
        }
        ediseed_representation = {"go": {"search": {"somewhere": "Z09"}}, "until": {"you find": "E01"}}
        edi_to_non_edi_domain_mapping: Dict[str, str] = {
            '$["a key"][0]["an entry"]': '$["go"]["search"]["somewhere"]',
            '$["another key"][2]["another entry"]': '$["until"]["you find"]',
        }
        # the following methods are just minimal examples. your application should define them
        def get_from_ediseed(edi_discriminator: str) -> Optional[str]:
            """
            finds data in the edifact data model ("EdiSeed")
            """
            return parse(edi_discriminator).find(ediseed_representation)[0].value

        def get_from_non_edifact(non_edi_discriminator: str) -> Optional[str]:
            """
            finds data in the non-edifact/application domain data model
            """
            return parse(non_edi_discriminator).find(non_edifact_representation)[0].value

        value_mapping = generate_value_pool_replacement(
            edifact_accessor=get_from_ediseed,
            non_edifact_accessor=get_from_non_edifact,
            edifact_to_non_edifact_path_mapping=edi_to_non_edi_domain_mapping,
        )
        data_element = DataElementValuePool(
            discriminator="foo",
            data_element_id="1153",
            entered_input=None,
            value_pool=[
                ValuePoolEntry(meaning="the meaning of Z09", ahb_expression="Muss [1]", qualifier="Z09"),
                ValuePoolEntry(meaning="the meaning of E01", ahb_expression="Muss [2]", qualifier="E01"),
            ],
        )
        data_element.replace_value_pool(value_mapping)
        assert data_element == DataElementValuePool(
            discriminator="foo",
            data_element_id="1153",
            entered_input=None,
            value_pool=[
                ValuePoolEntry(meaning="the meaning of Z09", ahb_expression="Muss [1]", qualifier="NON_EDIFACT_Z09"),
                ValuePoolEntry(meaning="the meaning of E01", ahb_expression="Muss [2]", qualifier="NON_EDIFACT_E01"),
            ],
        )
