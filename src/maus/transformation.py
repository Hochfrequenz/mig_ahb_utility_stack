"""
The transformation module is useful when you handle edifact transactions in both a domain/data model similar to edifact
(the "edifact domain") and a domain/data model which is used by your application (we simply call it the "non-edifact" or
"application domain").

Usually the data model similar to EDIFACT is something structurally equivalent to EDIFACT, think e.g. of a JSON or XML.
Wherever there is the possibility to group something in the form of repeated segment groups, you usually have something
like an array in your edifact-equivalent data structure. We call this structure an "EdiSeed", because it is what you
"seed" into your EdifactBuilder to generate EDIFACT. The transformation from an EdiSeed to EDIFACT is quite simple.
It's a plain mapping logic that doesn't care about cardinalities and more complicated stuff than simple replacements
and loops. Neighbouring segments in EDIFACT are transformed into neighbouring fields in the EdiSeed structure.
Think of the EdiSeed as an intermediate data structure.

MAUS is agnostic regarding your EdiSeed. It doesn't care about how your EdiSeed looks like exactly. It just needs to be
accessible somehow.

In your application you might use a different data model which is de-coupled from EDIFACT and thus also de-coupled from
the EdiSeed. This is generally a good idea, because it spares your application from the never-ending pain introduced by
BDEW and edi@energy every 6 months. However, this comes with the price of having to write a more complex transformation.

This module contains methods that are relevant when transforming data between your edi-similar structure ("EdiSeed")
and the application domain ("non-edifact").
"""
import asyncio
from typing import Any, Awaitable, Dict, List, Mapping, Optional, Protocol, TypeVar

from maus.models.anwendungshandbuch import DataElementValuePool, DeepAnwendungshandbuch
from maus.models.edifact_components import ValuePoolEntry

EdifactData = TypeVar("EdifactData")
"""
the type which you use to model the edifact side of things (e.g. the type of the EdiSeed)
"""
ApplicationData = TypeVar("ApplicationData")
"""
the type which you use to model the data in your application (e.g. the type of your BO4E, BOneyComb)
"""


class ApplicationEdifactConverter(Protocol[EdifactData, ApplicationData]):
    """
    this class describes a converter from the Application Domain to the EDIFACT Domain
    """

    async def transform_application_to_edi_domain(self, application_data: ApplicationData) -> EdifactData:
        """
        Transforms the given application data (e.g. bo4e/boneycomb) into the edifact domain (e.g. ediseed)
        :param application_data:
        :return: the converted data
        """

    async def transform_edi_to_application_domain(self, edifact_data: EdifactData) -> ApplicationData:
        """
        Transforms the given edifact data (e.g. ediseed) into the application domain (e.g. bo4e/boneycomb)
        :param edifact_data:
        :return: the converted data
        """


DataModel_contra = TypeVar("DataModel_contra", contravariant=True)


class Accessor(Protocol[DataModel_contra]):
    """description of a class that allows to get and set values from a generic data model"""

    def get_value(self, data: DataModel_contra, discriminator: str) -> Optional[Any]:
        """
        Gets the value described by the discriminator from the given data
        :param data: the data to be read
        :param discriminator: describes _which_ value should be read and returned
        :return: the value or None
        """

    def set_value(self, data: DataModel_contra, discriminator: str, value: Any) -> None:
        """
        Sets the value that is described by the disciminator in the given data instance.
        :param value: the value to be set
        :param data: the data to be modified
        :param discriminator: describes _which_ value should be set
        :return: nothing; it modifies the instance of data
        """


EdifactAccessor = Accessor[EdifactData]  #: a class that allows to access (read/write) in the edifact data model
ApplicationAccessor = Accessor[ApplicationData]  #: a class that allows to access (read/write) in the application data


# I feel like there's no way to boil this down to fewer arguments (6/5) without tradeoffs in readability.
# pylint:disable=too-many-arguments
async def generate_value_pool_replacement(
    application_data_model: ApplicationData,
    data_element: DataElementValuePool,
    converter: ApplicationEdifactConverter,
    edifact_accessor: EdifactAccessor,
    application_accessor: ApplicationAccessor,
    edifact_to_non_edifact_path_mapping: Mapping[str, str],
) -> Dict[str, str]:
    """
    generate the value pool replacement dict for the given data_element
    :param application_data_model: the application representation of the data
    :param data_element: the data_element for which the replacement shall be computed
    :param converter: a converter between application and edifact domain
    :param application_accessor: Allows to modify and access a given application data model
    :param edifact_accessor: Allows to modify and access a given edifact data model
    :param edifact_to_non_edifact_path_mapping: maps application domain (keys) to edifact domain (values) discriminators
    :return: a edifact (key) to non-edifact (value) mapping of values from the given data element value pool
    """
    initial_edifact_data = await converter.transform_application_to_edi_domain(application_data_model)
    edi_to_non_edi_value_mapping: Dict[str, str] = {}
    for edi_path, non_edi_path in edifact_to_non_edifact_path_mapping.items():
        if edi_path != data_element.discriminator:
            continue
        non_edi_value = application_accessor.get_value(application_data_model, non_edi_path)
        edi_value = edifact_accessor.get_value(
            initial_edifact_data, edi_path
        )  # this is the current value from the initial data
        if edi_value is not None:
            edi_to_non_edi_value_mapping.update({edi_value: non_edi_value})
        break
    else:
        raise ValueError(f"No mapping found for '{data_element.discriminator}'")

    # now loop over the other values
    async def _get_value_pool_mapping(value_pool_entry: ValuePoolEntry):
        # modified_edifact_data = initial_edifact_data.copy() #only works on dicts
        modified_edifact_data = initial_edifact_data  # ⚠ this modifies the reference!
        modified_edi_value = value_pool_entry.qualifier
        edifact_accessor.set_value(modified_edifact_data, edi_path, value_pool_entry.qualifier)
        # now we transform the modified edifact data back to the application domain
        modified_application_data = await converter.transform_edi_to_application_domain(modified_edifact_data)
        modified_application_value = application_accessor.get_value(modified_application_data, non_edi_path)
        return {modified_edi_value: modified_application_value}

    value_pool_mapping_tasks: List[Awaitable[Dict[str, Optional[str]]]] = [
        _get_value_pool_mapping(value_pool_entry) for value_pool_entry in data_element.value_pool
    ]
    for result in await asyncio.gather(*value_pool_mapping_tasks):
        edi_to_non_edi_value_mapping.update(result)
    return edi_to_non_edi_value_mapping


async def transform_all_value_pools(
    application_data_model: ApplicationData,
    deep_ahb: DeepAnwendungshandbuch,
    converter: ApplicationEdifactConverter,
    edifact_accessor: EdifactAccessor,
    application_accessor: ApplicationAccessor,
    edifact_to_non_edifact_path_mapping: Mapping[str, str],
) -> None:
    """
    transforms all value pools in the given deep ahb
    """
    replacement_tasks: List[Awaitable] = []

    async def transform_value_pool(value_pool: DataElementValuePool):
        replacement = await generate_value_pool_replacement(
            application_data_model=application_data_model,
            data_element=value_pool,
            converter=converter,
            edifact_accessor=edifact_accessor,
            application_accessor=application_accessor,
            edifact_to_non_edifact_path_mapping=edifact_to_non_edifact_path_mapping,
        )
        value_pool.replace_value_pool(replacement)

    for value_pool in deep_ahb.get_all_value_pools():
        # ignore Absender and Empfänger and all paths that are no json paths
        if (
            value_pool.discriminator is not None
            and value_pool.discriminator.startswith("$")
            and "Absender" not in value_pool.discriminator
            and "Empfänger" not in value_pool.discriminator
        ):
            replacement_tasks.append(transform_value_pool(value_pool))
    await asyncio.gather(*replacement_tasks)
