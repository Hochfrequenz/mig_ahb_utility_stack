# pylint:disable=too-few-public-methods
"""
This module contains classes that are required to model "Anwendungshandbücher" (AHB). There are two kinds of AHBs:
1. the "flat" AHB is very similar to the flat structure scraped from the official PDF files. It has no deep
structure.
2. the "nested" AHB which contains structural information (e.g. that a segment group is contained in
another segment group)
"""

from typing import List, Optional, Sequence
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
    ] = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(UUID))
    )  #: optional key
    # because the combination (segment group, segment, data element, name) is not guaranteed to be unique
    # yes, it's actually that bad already
    segment_group_key: Optional[str] = attr.ib(
        validator=attr.validators.optional(validator=attr.validators.instance_of(str))
    )
    """ the segment group, e.g. 'SG5' """

    segment_code: Optional[str] = attr.ib(
        validator=attr.validators.optional(validator=attr.validators.instance_of(str))
    )
    """the segment, e.g. 'IDE'"""

    data_element: Optional[str] = attr.ib(
        validator=attr.validators.optional(validator=attr.validators.instance_of(str))
    )
    """ the data element ID, e.g. '3224' """

    value_pool_entry: Optional[str] = attr.ib(
        validator=attr.validators.optional(validator=attr.validators.instance_of(str))
    )
    """ one of (possible multiple) allowed values, e.g. 'E01' or '293' """

    name: Optional[str] = attr.ib(validator=attr.validators.optional(validator=attr.validators.instance_of(str)))
    """the name, e.g. 'Meldepunkt'. It can be both the description of a field but also its meaning"""

    # Check the unittest test_csv_file_reading_11042 to see the different values of name. It's not only the grey fields
    # where user input is expected but also the meanings / values of value pool entries. This means the exact meaning of
    # name can only be determined in the context in which it is used. This is one of many shortcoming of the current AHB
    # structure: Things in the same column don't necessarily mean the same thing.
    ahb_expression: Optional[str] = attr.ib(
        validator=attr.validators.optional(validator=attr.validators.instance_of(str))
    )
    """a requirement indicator + an optional condition ("ahb expression"), f.e. 'Muss [123] O [456]' """

    # note: to parse expressions from AHBs consider using AHBicht: https://github.com/Hochfrequenz/ahbicht/

    def holds_any_information(self) -> bool:
        """
        Returns true iff the line holds any information exception for just a GUID.
        This is useful to filter out empty lines which are artefacts remaining from the scraping process.
        """
        return (
            (self.segment_group_key is not None and len(self.segment_group_key.strip()) > 0)
            or (self.segment_code is not None and len(self.segment_code.strip()) > 0)
            or (self.data_element is not None and len(self.data_element.strip()) > 0)
            or (self.value_pool_entry is not None and len(self.value_pool_entry.strip()) > 0)
            or (self.name is not None and len(self.name.strip()) > 0)
            or (self.ahb_expression is not None and len(self.ahb_expression.strip()) > 0)
        )

    def get_discriminator(self, include_name: bool = True) -> str:
        """
        Generate a unique yet readable discriminator for this given line.
        This discriminator is generated just from the line itself without any information on where it occurs.
        It does neither know its position inside the AHB nor parent or sub groups.
        """
        result: str
        if self.segment_group_key:
            result = f"{self.segment_group_key}->"
        else:
            result = ""
        result += f"{self.segment_code}->{self.data_element}"
        if self.name and include_name:
            result += f" ({self.name})"
        return result


class AhbLineSchema(Schema):
    """
    A schema to (de-)serialize :class:`.AhbLine`
    """

    guid = fields.UUID(required=False, load_default=None)
    segment_group_key = fields.String(required=False, load_default=None)
    segment_code = fields.String(required=False, load_default=None)
    data_element = fields.String(required=False, load_default=None)
    value_pool_entry = fields.String(required=False, load_default=None)
    name = fields.String(required=False, load_default=None)
    ahb_expression = fields.String(required=False, load_default=None)

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
    Meta information about an AHB like f.e. its title, Prüfidentifikator, possible sender and receiver roles
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

    meta: AhbMetaInformation = attr.ib(validator=attr.validators.instance_of(AhbMetaInformation))
    """information about this AHB"""

    lines: List[AhbLine] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(AhbLine), iterable_validator=attr.validators.instance_of(list)
        )
    )  #: ordered list lines as they occur in the AHB

    def get_segment_groups(self) -> List[Optional[str]]:
        """
        :return: a set with all segment groups in this AHB in the order in which they occur
        """
        return FlatAnwendungshandbuch._get_available_segment_groups(self.lines)

    @staticmethod
    def _get_available_segment_groups(lines: List[AhbLine]) -> List[Optional[str]]:
        """
        extracts the distinct segment groups from a list of ahb lines
        :param lines:
        :return: distinct segment groups, including None in the order in which they occur
        """
        # this code is in a static method to make it easily accessible for fine grained unit testing
        result: List[Optional[str]] = []
        for line in lines:
            if line.segment_group_key not in result:
                # an "in" check against a set would be faster but we want to preserve both order and readability
                result.append(line.segment_group_key)
        return result

    def sort_lines_by_segment_groups(self):
        """
        sorts lines by segment groups while preserving the order inside the groups and the order between the groups.
        """
        self.lines = FlatAnwendungshandbuch._sorted_lines_by_segment_groups(self.lines, self.get_segment_groups())

    @staticmethod
    def _sorted_lines_by_segment_groups(ahb_lines: Sequence[AhbLine], sg_order: List[Optional[str]]) -> List[AhbLine]:
        """
        Calls sorted(...) on the provided list and returns a new list.
        Its purpose is, that if a segment group in the AHB (read from top to bottom in the flat ahb/pdf) is interrupted
        by other segment groups, the lines belonging to the same group will be next to each other.
        This is useful to later use a groupby aggregation that only returns one group key per segment group.

        The sort is stable such that the existing order inside the segment groups is maintained.

        Note that this also means, that the order of the return lines no longer the same as in the flat AHB.

        If you provide this function a list:
        [
            (SG2, Foo),
            (SG2, Bar),
            (SG3, ABC),
            (SG3, DEF),
            (SG2, SomethingElse)
        ]
        The result will be:
        [
            (SG2, Foo),
            (SG2, Bar),
            (SG2, SomethingElse)
            (SG3, ABC),
            (SG3, DEF)
        ]

        See the unittests for details.
        """

        # this code is in a static method to make it easily accessible for fine grained unit testing
        result: List[AhbLine] = sorted(ahb_lines, key=lambda x: x.segment_group_key or "")
        result.sort(key=lambda ahb_line: sg_order.index(ahb_line.segment_group_key))
        return result


class FlatAnwendungshandbuchSchema(Schema):
    """
    A schema to (de-)serialize :class:`.FlatAnwendungshandbuch`
    """

    meta = fields.Nested(AhbMetaInformationSchema)
    lines = fields.List(fields.Nested(AhbLineSchema))

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> FlatAnwendungshandbuch:
        """
        Converts the barely typed data dictionary into an actual :class:`.FlatAnwendungshandbuch`
        """
        return FlatAnwendungshandbuch(**data)


@attr.s(auto_attribs=True, kw_only=True)
class DeepAnwendungshandbuch:
    """
    The data of the AHB nested as described in the MIG.
    """

    meta: AhbMetaInformation = attr.ib(validator=attr.validators.instance_of(AhbMetaInformation))
    """information about this AHB"""

    lines: List[SegmentGroup] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(SegmentGroup),
            iterable_validator=attr.validators.instance_of(list),
        )
    )  #: the nested data


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
