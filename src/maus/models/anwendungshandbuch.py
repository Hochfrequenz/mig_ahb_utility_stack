# pylint:disable=too-few-public-methods
"""
This module contains classes that are required to model "Anwendungshandbücher" (AHB). There are two kinds of AHBs:
1. the "flat" AHB is very similar to the flat structure scraped from the official PDF files. It has no deep
structure.
2. the "nested" AHB which contains structural information (e.g. that a segment group is contained in
another segment group)
"""

from typing import List, Optional, Set
from uuid import UUID

import attr
from marshmallow import Schema, fields, post_load  # type:ignore[import]

from maus.models.edifact_components import SegmentGroup, SegmentGroupSchema


@attr.s(auto_attribs=True, kw_only=True)
class AhbLine:
    """
    An AhbLine is a single line inside the machine readable, flat AHB.
    """

    guid: Optional[
        UUID
        # pylint: disable=line-too-long
    ]  #: optional key
    # because the combination (segment group, segment, data element, name) is not guaranteed to be unique
    # yes, it's actually that bad already
    segment_group: Optional[str]  #: the segment group, e.g. "SG5"
    segment: Optional[str]  #: the segment, e.g. "IDE"
    data_element: Optional[str]  #: the data element ID, e.g. "3224"
    value_pool_entry: Optional[str]  #: one of (possible multiple) allowed values, e.g. "E01" or "293"
    name: Optional[str]  #: the name, e.g. "Meldepunkt"
    ahb_expression: Optional[
        str
    ]  #: a requirement indicator + an optional condition ("ahb expression"), f.e. "Muss [123] O [456]"

    # note: to parse expressions from AHBs consider using AHBicht: https://github.com/Hochfrequenz/ahbicht/

    def get_discriminator(self, include_name: bool = True) -> str:
        """
        Generate a unique yet readable discriminator for this given line
        """
        result: str
        if self.segment_group:
            result = f"{self.segment_group}->"
        else:
            result = ""
        result += f"{self.segment}->{self.data_element}"
        if self.name and include_name:
            result += f" ({self.name})"
        return result


class AhbLineSchema(Schema):
    """
    A schema to (de-)serialize :class:`.AhbLine`
    """

    guid = fields.UUID(required=False, missing=None)
    segment_group = fields.String(required=False, missing=None)
    segment = fields.String(required=False, missing=None)
    data_element = fields.String(required=False, missing=None)
    value_pool_entry = fields.String(required=False, missing=None)
    name = fields.String(required=False, missing=None)
    ahb_expression = fields.String(required=False, missing=None)

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> AhbLine:
        """
        Converts the barely typed data dictionary into an actual :class:`.AhbLine`
        """
        return AhbLine(**data)


@attr.s(auto_attribs=True, kw_only=True)
class AhbMetaInformation:
    """
    Meta information about an AHB like f.e. Its title, Prüfidentifikator, possible sender and receiver roles
    """

    pruefidentifikator: str  #: identifies the message type (within a fixed format version) e.g. "11042" or "13012"
    # there's more to come  but for now we'll leave it as is, because we're just in a proof of concept phase


class AhbMetaInformationSchema(Schema):
    """
    A schema to (de-)serialize :class:`.AhbMetaInformation`
    """

    pruefidentifikator = fields.String(required=True)

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> AhbMetaInformation:
        """
        Converts the barely typed data dictionary into an actual :class:`.AhbMetaInformation`
        """
        return AhbMetaInformation(**data)


@attr.s(auto_attribs=True, kw_only=True)
class FlatAnwendungshandbuch:
    """
    A flat Anwendungshandbuch (AHB) models an Anwendungshandbuch as combination of some meta data and an ordered list
    of `.class:`.FlatAhbLine s. Basically a flat Anwendungshandbuch is the result of a simple scraping approach.
    You can create instances of this class without knowing anything about the "under the hood" structure of AHBs or MIGs
    """

    meta: AhbMetaInformation  #: information about this AHB
    lines: List[AhbLine]  #: ordered list lines as they occur in the AHB

    def get_segment_groups(self):
        """

        :return: a set with all segment groups in this AHB
        """
        return FlatAnwendungshandbuch._get_available_segment_groups(self.lines)

    @staticmethod
    def _get_available_segment_groups(lines: List[AhbLine]) -> Set[Optional[str]]:
        """
        extracts the distinct segment groups from a list of ahb lines
        :param lines:
        :return: distinct segment groups, including None
        """
        return {line.segment_group for line in lines if lines}


class FlatAnwendungshandbuchSchema(Schema):
    """
    A schema to (de-)serialize :class:`.Anwendungshandbuch`
    """

    meta = fields.Nested(AhbMetaInformationSchema)
    lines = fields.List(fields.Nested(AhbLineSchema))

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> FlatAnwendungshandbuch:
        """
        Converts the barely typed data dictionary into an actual :class:`.Anwendungshandbuch`
        """
        return FlatAnwendungshandbuch(**data)


@attr.s(auto_attribs=True, kw_only=True)
class DeepAnwendungshandbuch:
    """
    The data of the AHB nested as described in the MIG.
    """

    meta: AhbMetaInformation  #: information about this AHB
    lines: List[SegmentGroup]  #: the nested data


class DeepAnwendungshandbuchSchema(Schema):
    """
    A schema to (de-)serialize :class:`.DeepAnwendungshandbuch`
    """

    meta = fields.Nested(AhbMetaInformationSchema)
    lines = fields.List(fields.Nested(SegmentGroupSchema))

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> DeepAnwendungshandbuch:
        """
        Converts the barely typed data dictionary into an actual :class:`.DeepAnwendungshandbuch`
        """
        return DeepAnwendungshandbuch(**data)
