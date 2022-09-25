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
from typing import Any, Awaitable, Callable, Dict, List, Mapping, Optional, TypeVar

from maus import DataElementValuePool, ValuePoolEntry

EdifactData = TypeVar("EdifactData")
"""
the type which you use to model the edifact side of things (e.g. the type of the EdiSeed)
"""
ApplicationData = TypeVar("ApplicationData")
"""
the type which you use to model the data in your application (e.g. the type of your BO4E, BOneyComb)
"""

# todo: fix all the linter warnings in this method
async def generate_value_pool_replacement(
    application_data_model: ApplicationData,
    data_element: DataElementValuePool,
    transform_application_to_edi_domain: Callable[[ApplicationData], Awaitable[EdifactData]],
    transform_edi_to_application_domain: Callable[[EdifactData], Awaitable[ApplicationData]],
    get_edifact_value: Callable[[EdifactData, str], Optional[Any]],
    get_application_value: Callable[[ApplicationData, str], Optional[Any]],
    set_edifact_value: Callable[[EdifactData, str, Any], None],
    # set_application_value: Callable[[TApplicationData, str, Any], None],
    edifact_to_non_edifact_path_mapping: Mapping[str, str],
) -> Dict[str, str]:
    """
    generate the value pool replacement dict for the given data_element
    :param application_data_model: the application representation of the data
    :param data_element: the data_element for which the replacement shall be computed
    :param transform_application_to_edi_domain: function to transform application data (e.g. bo4e) to ediseed
    :param transform_edi_to_application_domain:  function to transform ediseed to application data (e.g. bo4e)
    :param get_edifact_value: returns value for given edifact discriminator
    :param get_application_value: returns value for given application data model discriminator
    :param set_edifact_value: set the value in the edifact domain
    :param edifact_to_non_edifact_path_mapping: maps application domain (keys) to edifact domain (values) discriminators
    :return: a edifact (key) to non-edifact (value) mapping of values from the given data element value pool
    """
    initial_edifact_data = await transform_application_to_edi_domain(application_data_model)
    edi_to_non_edi_value_mapping: Dict[str, str] = {}
    for edi_path, non_edi_path in edifact_to_non_edifact_path_mapping.items():
        if edi_path != data_element.discriminator:
            continue
        non_edi_value = get_application_value(application_data_model, non_edi_path)
        edi_value = get_edifact_value(initial_edifact_data, edi_path)  # this is the current value from the initial data
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
        set_edifact_value(modified_edifact_data, edi_path, value_pool_entry.qualifier)
        # now we transform the modified edifact data back to the application domain
        modified_application_data = await transform_edi_to_application_domain(modified_edifact_data)
        modified_application_value = get_application_value(modified_application_data, non_edi_path)
        return {modified_edi_value: modified_application_value}

    value_pool_mapping_tasks: List[Awaitable[Dict[str, Optional[str]]]] = []
    for value_pool_entry in data_element.value_pool:
        value_pool_mapping_tasks.append(_get_value_pool_mapping(value_pool_entry))
    results = await asyncio.gather(*value_pool_mapping_tasks)
    for result in results:
        edi_to_non_edi_value_mapping.update(result)
    return edi_to_non_edi_value_mapping
