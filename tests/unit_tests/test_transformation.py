from typing import Any, Optional

import pytest  # type:ignore[import]
from jsonpath_ng.ext import parse  # type:ignore[import] #  jsonpath is just installed in the tests

from maus.models.edifact_components import DataElementValuePool, ValuePoolEntry
from maus.transformation import generate_value_pool_replacement


def _get_value_using_json_path(data: dict, path: str) -> Optional[Any]:
    return parse(path).find(data)[0].value


def get_value_from_application_domain(application_data: dict, application_discriminator: str) -> Optional[str]:
    """
    finds data in the non-edifact/application domain data model
    """
    return _get_value_using_json_path(application_data, application_discriminator)


def get_value_from_edifact_domain(edifact_data: dict, edi_discriminator: str) -> Optional[str]:
    """
    finds data in the edifact data model ("EdiSeed")
    """
    return _get_value_using_json_path(edifact_data, edi_discriminator)


def _set_value_using_json_path(data: dict, path: str, new_value: Any) -> None:
    current_datum = parse(path).find(data)[0]
    current_datum.full_path.update(data, new_value)


def set_value_from_application_domain(application_data: dict, application_discriminator: str, new_value: Any) -> None:
    """
    finds data in the non-edifact/application domain data model and replaces them with new_value.
    This modifies the application_data instance.
    """
    _set_value_using_json_path(data=application_data, path=application_discriminator, new_value=new_value)


def set_value_from_edifact_domain(edifact_data: dict, edi_discriminator: str, new_value: Any) -> None:
    """
    finds data in the edifact domain data model ("EdiSeed") and replaces them with new_value.
    This modifies the edifact_data instance.
    """
    _set_value_using_json_path(data=edifact_data, path=edi_discriminator, new_value=new_value)


class TestTransformation:
    async def test_value_pool_mapping_mwe(self):
        application_domain_data = {
            "noise": "foo",
            "transaktionsdaten": {
                "transaktionsgrund": None,
            },
        }  #: some data to start with, e.g. entered by a user in a frontend, hardcoded, whatever
        edi_to_application_data_model_mapping = {
            "$['Transaktionsgrund']": "$['transaktionsdaten']['transaktionsgrund']",
            "$['EdiFoo']": "$['stammdaten'][0]['applicationFoo']",
            "$['TheThing']['TheProperty']": "$['stammdaten'][0]['theProperty']",
            "$['TheThing']['AnotherProperty']": "$['stammdaten'][0]['anotherProperty']",
        }  #: a mapping that allows us to find data in both application and edifact domain

        data_element = DataElementValuePool(
            discriminator="$['Transaktionsgrund']",  # this is the original edifact domain discriminator
            data_element_id="1234",
            entered_input=None,
            value_pool=[
                ValuePoolEntry(meaning="the meaning of E01 from the AHB", ahb_expression="Muss [1]", qualifier="E01"),
                ValuePoolEntry(meaning="the meaning of E02 from the AHB", ahb_expression="Muss [2]", qualifier="E02"),
                ValuePoolEntry(meaning="the meaning of E03 from the AHB", ahb_expression="Muss [3]", qualifier="E03"),
            ],
        )

        async def generate_edi_represenation(application_domain_dict: dict):
            """
            Generate the edifact representations from the given application_domain_data.
            In real life this should call the transformation application➡edifact data model mapping logic.
            This is just a stub with hardcoded mappings.
            """
            # in real live this should call the transformer (edifact ↔ non-edifact)
            transaktionsgrund_application_domain = application_domain_dict["transaktionsdaten"]["transaktionsgrund"]
            application_to_edi_mapping_transaktionsgrund = {"EINZUG": "E01", "NEUANLAGE": "E02", "WECHSEL": "E03"}
            try:
                edifact_transaktionsgrund = application_to_edi_mapping_transaktionsgrund[
                    transaktionsgrund_application_domain
                ]
            except KeyError:
                edifact_transaktionsgrund = None

            return {  # data in edifact domain
                "Transaktionsgrund": edifact_transaktionsgrund,
                "EdiFoo": "EdiBar",
                "TheThing": {"TheProperty": "Value1", "AnotherProperty": "AnotherValue"},
            }

        async def generate_application_represenation(edifact_seed: dict):
            """
            Generate the application representations from the given edifact seed.
            In real life this should call the transformation edifact➡application data model mapping logic.
            This is just a stub with hardcoded mappings.
            """
            transaktionsgrund_edifact_domain = edifact_seed["Transaktionsgrund"]
            edi_to_application_mapping_transaktionsgrund = {"E01": "EINZUG", "E02": "NEUANLAGE", "E03": "WECHSEL"}
            try:
                application_transaktionsgrund = edi_to_application_mapping_transaktionsgrund[
                    transaktionsgrund_edifact_domain
                ]
            except KeyError:
                application_transaktionsgrund = None

            return {
                "noise": "foo",
                "transaktionsdaten": {
                    "transaktionsgrund": application_transaktionsgrund,
                },
            }

        value_mapping = await generate_value_pool_replacement(
            application_data_model=application_domain_data,
            data_element=data_element,
            get_edifact_value=get_value_from_edifact_domain,
            get_application_value=get_value_from_application_domain,
            set_edifact_value=set_value_from_edifact_domain,
            # set_application_value=set_value_from_application_domain,
            transform_application_to_edi_domain=generate_edi_represenation,
            transform_edi_to_application_domain=generate_application_represenation,
            edifact_to_non_edifact_path_mapping=edi_to_application_data_model_mapping,
        )
        data_element.replace_value_pool(value_mapping)
        assert data_element == DataElementValuePool(
            discriminator="$['Transaktionsgrund']",
            data_element_id="1234",
            entered_input=None,
            value_pool=[
                # here we got the application (e.g. bo4e) qualifiers with the respective expressions from the AHB
                ValuePoolEntry(
                    meaning="the meaning of E01 from the AHB", ahb_expression="Muss [1]", qualifier="EINZUG"
                ),
                ValuePoolEntry(
                    meaning="the meaning of E02 from the AHB", ahb_expression="Muss [2]", qualifier="NEUANLAGE"
                ),
                ValuePoolEntry(
                    meaning="the meaning of E03 from the AHB", ahb_expression="Muss [3]", qualifier="WECHSEL"
                ),
            ],
        )
