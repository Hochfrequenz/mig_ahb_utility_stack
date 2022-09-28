from typing import Any, Optional

import pytest  # type:ignore[import]
from jsonpath_ng.ext import parse  # type:ignore[import] #  jsonpath is just installed in the tests

from maus import DeepAnwendungshandbuch
from maus.models.anwendungshandbuch import AhbMetaInformation
from maus.models.edifact_components import (
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)
from maus.transformation import generate_value_pool_replacement, transform_all_value_pools


def _get_value_using_json_path(data: dict, path: str) -> Optional[Any]:
    return parse(path).find(data)[0].value


def _set_value_using_json_path(data: dict, path: str, new_value: Any) -> None:
    current_datum = parse(path).find(data)[0]
    current_datum.full_path.update(data, new_value)


class DummyApplicationAccessor:
    # a class that obeys the type hints of the transformation.ApplicationAccessor
    def get_value(self, application_data: dict, application_discriminator: str) -> Optional[str]:
        """
        finds data in the non-edifact/application domain data model
        """
        return _get_value_using_json_path(application_data, application_discriminator)

    def set_value(self, _: dict, __: str) -> None:
        raise NotImplementedError("Not needed as of now")


class DummyEdifactAccessor:
    # a class that obeys the type hints of the transformation.EdifactAccessor
    def get_value(self, edifact_data: dict, edi_discriminator: str) -> Optional[str]:
        """
        finds data in the edifact data model ("EdiSeed")
        """
        return _get_value_using_json_path(edifact_data, edi_discriminator)

    def set_value(self, edifact_data: dict, edi_discriminator: str, new_value: Any) -> None:
        """
        finds data in the edifact domain data model ("EdiSeed") and replaces them with new_value.
        This modifies the edifact_data instance.
        """
        _set_value_using_json_path(data=edifact_data, path=edi_discriminator, new_value=new_value)


class DummyBo4eEdifactConverter:
    """this converter obeys the protocol of transformation.ApplicationEdifactConverter"""

    async def transform_application_to_edi_domain(self, application_domain_dict: dict):
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

    async def transform_edi_to_application_domain(self, edifact_seed: dict):
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
        converter = DummyBo4eEdifactConverter()
        edifact_accessor = DummyEdifactAccessor()
        application_accessor = DummyApplicationAccessor()
        value_mapping = await generate_value_pool_replacement(
            application_data_model=application_domain_data,
            data_element=data_element,
            converter=converter,
            edifact_accessor=edifact_accessor,
            application_accessor=application_accessor,
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
        assert application_domain_data == {
            "noise": "foo",
            "transaktionsdaten": {
                "transaktionsgrund": None,
            },
        }  # the original data should not have been modified

    async def test_value_pool_mapping_in_deep_ahb(self):
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

        deep_ahb = DeepAnwendungshandbuch(
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
                                    discriminator="$['Transaktionsgrund']",
                                    # this is the original edifact domain discriminator
                                    data_element_id="1234",
                                    entered_input=None,
                                    value_pool=[
                                        ValuePoolEntry(
                                            meaning="the meaning of E01 from the AHB",
                                            ahb_expression="Muss [1]",
                                            qualifier="E01",
                                        ),
                                        ValuePoolEntry(
                                            meaning="the meaning of E02 from the AHB",
                                            ahb_expression="Muss [2]",
                                            qualifier="E02",
                                        ),
                                        ValuePoolEntry(
                                            meaning="the meaning of E03 from the AHB",
                                            ahb_expression="Muss [3]",
                                            qualifier="E03",
                                        ),
                                    ],
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
        )
        converter = DummyBo4eEdifactConverter()
        edifact_accessor = DummyEdifactAccessor()
        application_accessor = DummyApplicationAccessor()
        await transform_all_value_pools(
            application_data_model=application_domain_data,
            deep_ahb=deep_ahb,
            converter=converter,
            edifact_accessor=edifact_accessor,
            application_accessor=application_accessor,
            edifact_to_non_edifact_path_mapping=edi_to_application_data_model_mapping,
        )
        assert deep_ahb.get_all_value_pools()[0] == DataElementValuePool(
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
        assert application_domain_data == {
            "noise": "foo",
            "transaktionsdaten": {
                "transaktionsgrund": None,
            },
        }  # the original data should not have been modified
