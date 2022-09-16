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

MAUS is agnostic regarding you EdiSeed. It doesn't care about how your EdiSeed looks like exactly. It just needs to be
accessible somehow.

In your application you might use a different data model which is de-coupled from EDIFACT and thus also de-coupled from
the EdiSeed. This is generally a good idea, because it spares your application from the never-ending pain introduced by
BDEW and edi@energy every 6 months. However, this comes with the price of having to write a more complex transformation.

This module contains methods that are relevant when transforming data between your edi-similar structure ("EdiSeed")
and the application domain ("non-edifact").
"""
from typing import Any, Callable, Dict, Mapping, Optional


def generate_value_pool_replacement(
    edifact_accessor: Callable[[str], Optional[Any]],
    non_edifact_accessor: Callable[[str], Optional[Any]],
    edifact_to_non_edifact_path_mapping: Mapping[str, str],
) -> Dict[str, str]:
    """
    When there is a value pool in an AHB, you might have a similar value pool in your application domain.
    Both the edifact and the non-edifact value pool elements can be found by using a respective accessor method.
    :param edifact_accessor: function to get a value from the edifact-data structure
    :param non_edifact_accessor: function to get a value from the non edifact-data structure
    :param edifact_to_non_edifact_path_mapping: a mapping from unique discriminators in the edifact data structure to
    the discriminators in the application data model
    :return: a dictionary which can be used to replace elements in the value pool.
    """
    edi_to_non_edi_value_mapping: Dict[str, str] = {}
    for non_edi_path, edi_path in edifact_to_non_edifact_path_mapping.items():
        non_edi_value = non_edifact_accessor(non_edi_path)
        if non_edi_value is None:
            continue
        edi_value = edifact_accessor(edi_path)
        if edi_value is None:
            continue
        edi_to_non_edi_value_mapping.update({edi_value: non_edi_value})
    # todo: i think this function does not account for real world complexity yet. we should write an integration test
    return edi_to_non_edi_value_mapping
