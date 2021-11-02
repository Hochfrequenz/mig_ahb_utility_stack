from typing import List, Optional, Union

import attr


@attr.s(auto_attribs=True)
class MessageImplementationGuide:
    """
    A Message Implementation Guide (MIG) describes the structure of messages in a certain EDIFACT format (e.g. UTILMD 5.2a)
    """

    mig_json: Union[dict, list]


@attr.s(auto_attribs=True)
class AhbLine:
    """
    An AhbLine is a single line inside the machine redable AHB
    """

    segment_group: Optional[str]  # the segment group, e.g. "SG5"
    segment: Optional[str]  # the segment, e.g. "IDE"
    data_element: Optional[str]  # the data element ID, e.g. "3224"
    name: Optional[str]  # the name, e.g. "Meldepunkt"
    ahb_expression: Optional[str]  # a modal mark + an optional condition ("ahb expression"), f.e. "Muss [123] O [456]"
    # note: to parse expressions from AHBs consider using AHBicht: https://github.com/Hochfrequenz/ahbicht/


@attr.s(auto_attribs=True)
class Anwendungshandbuch:
    """
    An Anwendungshandbuch (AHB) describes the structure of a message and which data are required under which circumstances.
    It is basically a list of AhbLines + some meta information
    """

    pruefidentifikator: str  # e.g. "11042" or "13012"
    lines: List[AhbLine]  # ordered list of AHblines


class MigAhbUtilityStack:
    def __init__(self, mig: MessageImplementationGuide, ahb: Anwendungshandbuch):
        self._mig: MessageImplementationGuide = mig
        self._ahb: Anwendungshandbuch = ahb
