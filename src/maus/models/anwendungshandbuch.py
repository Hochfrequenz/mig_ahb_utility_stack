# pylint:disable=too-few-public-methods
"""
This module contains classes that are required to model "Anwendungshandbücher" (AHB). There are two kinds of AHBs:
1. the "flat" AHB is very similar to the flat structure scraped from the official PDF files. It has no deep
structure.
2. the "nested" AHB which contains structural information (e.g. that a segment group is contained in
another segment group)
"""

from typing import Callable, List, Optional, Sequence, Set
from uuid import UUID

import attr.validators
import attrs
from marshmallow import Schema, fields, post_load  # type:ignore[import]

from maus.models.edifact_components import (
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    SegmentGroupSchema,
)


# pylint:disable=too-many-instance-attributes
@attrs.define(auto_attribs=True, kw_only=True)
class AhbLine:
    """
    An AhbLine is a single line inside the machine-readable, flat AHB.
    """

    guid: Optional[UUID] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(UUID))
    )  #: optional key
    # because the combination (segment group, segment, data element, name) is not guaranteed to be unique
    # yes, it's actually that bad already
    segment_group_key: Optional[str] = attrs.field(
        validator=attrs.validators.optional(validator=attrs.validators.instance_of(str))
    )
    """ the segment group, e.g. 'SG5' """

    segment_code: Optional[str] = attrs.field(
        validator=attrs.validators.optional(validator=attrs.validators.instance_of(str))
    )
    """the segment, e.g. 'IDE'"""

    data_element: Optional[str] = attrs.field(
        validator=attrs.validators.optional(validator=attrs.validators.instance_of(str))
    )
    """ the data element ID, e.g. '3224' """

    value_pool_entry: Optional[str] = attrs.field(
        validator=attrs.validators.optional(validator=attrs.validators.instance_of(str))
    )
    """ one of (possible multiple) allowed values, e.g. 'E01' or '293' """

    name: Optional[str] = attrs.field(validator=attrs.validators.optional(validator=attrs.validators.instance_of(str)))
    """the name, e.g. 'Meldepunkt'. It can be both the description of a field but also its meaning"""

    # Check the unittest test_csv_file_reading_11042 to see the different values of name. It's not only the grey fields
    # where user input is expected but also the meanings / values of value pool entries. This means the exact meaning of
    # name can only be determined in the context in which it is used. This is one of many shortcoming of the current AHB
    # structure: Things in the same column don't necessarily mean the same thing.
    ahb_expression: Optional[str] = attrs.field(
        validator=attrs.validators.optional(validator=attrs.validators.instance_of(str))
    )
    """a requirement indicator + an optional condition ("ahb expression"), e.g. 'Muss [123] O [456]' """
    # note: to parse expressions from AHBs consider using AHBicht: https://github.com/Hochfrequenz/ahbicht/

    section_name: Optional[str] = attrs.field(
        validator=attrs.validators.optional(validator=attrs.validators.instance_of(str)), default=None
    )
    """
    The section name describes the purpose of a segment, e.g. "Nachrichten-Kopfsegment" or "Beginn der Nachricht"
    """

    def holds_any_information(self) -> bool:
        """
        Returns true iff the line holds any information exception for just a GUID.
        This is useful to filter out empty lines which are artefacts remaining from the scraping process.
        """
        # https://stackoverflow.com/questions/47972143/using-attr-with-pylint
        # pylint: disable=no-member
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
    section_name = fields.String(required=False, load_default=None)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> AhbLine:
        """
        Converts the barely typed data dictionary into an actual :class:`.AhbLine`
        """
        return AhbLine(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class AhbMetaInformation:
    """
    Meta information about an AHB like e.g. its title, Prüfidentifikator, possible sender and receiver roles
    """

    pruefidentifikator: str  #: identifies the message type (within a fixed format version) e.g. "11042" or "13012"
    # there's more to come  but for now we'll leave it as is, because we're just in a proof of concept phase


class AhbMetaInformationSchema(Schema):
    """
    A schema to (de-)serialize :class:`.AhbMetaInformation`
    """

    pruefidentifikator = fields.String(required=True)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> AhbMetaInformation:
        """
        Converts the barely typed data dictionary into an actual :class:`.AhbMetaInformation`
        """
        return AhbMetaInformation(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class FlatAnwendungshandbuch:
    """
    A flat Anwendungshandbuch (AHB) models an Anwendungshandbuch as combination of some meta data and an ordered list
    of `.class:`.FlatAhbLine s. Basically a flat Anwendungshandbuch is the result of a simple scraping approach.
    You can create instances of this class without knowing anything about the "under the hood" structure of AHBs or MIGs
    """

    meta: AhbMetaInformation = attrs.field(validator=attrs.validators.instance_of(AhbMetaInformation))
    """information about this AHB"""

    lines: List[AhbLine] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(AhbLine),
            iterable_validator=attrs.validators.instance_of(list),
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

        # this code is in a static method to make it easily accessible for fine-grained unit testing
        result: List[AhbLine] = sorted(ahb_lines, key=lambda x: x.segment_group_key or "")
        result.sort(key=lambda ahb_line: sg_order.index(ahb_line.segment_group_key))
        return result


class FlatAnwendungshandbuchSchema(Schema):
    """
    A schema to (de-)serialize :class:`.FlatAnwendungshandbuch`
    """

    meta = fields.Nested(AhbMetaInformationSchema)
    lines = fields.List(fields.Nested(AhbLineSchema))

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> FlatAnwendungshandbuch:
        """
        Converts the barely typed data dictionary into an actual :class:`.FlatAnwendungshandbuch`
        """
        return FlatAnwendungshandbuch(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class DeepAhbInputReplacement:
    """
    A container class that models replacements of inputs in the DeepAnwendungshandbuch
    """

    #: true iff a replacement is applicable
    replacement_found: bool = attrs.field(validator=attrs.validators.instance_of(bool))
    input_replacement: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attr.validators.instance_of(str))
    )
    """
    The replacement for entered_input itself. Note that the replacement may be None even if a replacement is found.
    This implies, that you must always check for replacement_found is True first and then, iff true, replace with the
    replacement, even if it may be None/null.
    """


@attrs.define(auto_attribs=True, kw_only=True)
class DeepAnwendungshandbuch:
    """
    The data of the AHB nested as described in the MIG.
    """

    meta: AhbMetaInformation = attrs.field(validator=attrs.validators.instance_of(AhbMetaInformation))
    """information about this AHB"""

    lines: List[SegmentGroup] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(SegmentGroup),
            iterable_validator=attrs.validators.instance_of(list),
        )
    )  #: the nested data

    @staticmethod
    def _query_segment_group(
        segment_group: SegmentGroup, predicate: Callable[[SegmentGroup], bool]
    ) -> List[SegmentGroup]:
        """
        recursively search for a segment group that matches the predicate
        :return: return empty list if nothing was found, the matching segment groups otherwise
        """
        result: List[SegmentGroup] = []
        if predicate(segment_group):
            result.append(segment_group)
        if segment_group.segment_groups is not None:
            for sub_group in segment_group.segment_groups:
                sub_result = DeepAnwendungshandbuch._query_segment_group(sub_group, predicate)
                result += sub_result
        return result

    def find_segment_groups(self, predicate: Callable[[SegmentGroup], bool]) -> List[SegmentGroup]:
        """
        recursively search for segment group in this ahb that meets the predicate.
        :return: list of segment groups that match the predicate; empty list otherwise
        """
        result: List[SegmentGroup] = []
        for line in self.lines:
            if line.segment_groups is not None:
                for segment_group in line.segment_groups:
                    result += DeepAnwendungshandbuch._query_segment_group(segment_group, predicate)
            for line_result in DeepAnwendungshandbuch._query_segment_group(line, predicate):
                if line_result not in result:
                    result.append(line_result)
        return result

    def find_segments(
        self,
        group_predicate: Callable[[SegmentGroup], bool] = lambda _: True,
        segment_predicate: Callable[[Segment], bool] = lambda _: True,
    ) -> List[Segment]:
        """
        recursively search for segment characterised by the segment_predicate inside a group characterised by the
        group_predicate.
        :return: list of matching segments, empty list if nothing was found
        """
        result: List[Segment] = []
        for segment_group in self.find_segment_groups(group_predicate):
            result += segment_group.find_segments(segment_predicate)
        for line in self.lines:
            if line.segments is not None:
                for segment in line.segments:
                    if segment_predicate(segment):
                        result.append(segment)
        return result

    def replace_inputs_based_on_discriminator(self, replacement_func: Callable[[str], DeepAhbInputReplacement]) -> None:
        """
        Replace all the entered_inputs in the entire DeepAnwendungshandbuch using the given replacement_func.
        Note that this modifies this DeepAnwendungshandbuch instance (self).
        """
        _replace_inputs_based_on_discriminator(self.lines, replacement_func)

    def get_all_value_pools(self) -> List[DataElementValuePool]:
        """
        recursively find all value pools in the deep ahb
        :return: a list of all value pools
        """
        result: List[DataElementValuePool] = []
        added_discriminators: Set[str] = set()  # checks like "str in set" are way faster than "value pool in list"

        def add_to_result(value_pool: DataElementValuePool):
            if value_pool.discriminator in added_discriminators:
                # assumption: the discriminator is truly unique in an AHB
                return
            if value_pool not in result:
                added_discriminators.add(value_pool.discriminator)
                result.append(value_pool)

        for segment in self.find_segments():
            for sub_result in segment.get_all_value_pools():
                add_to_result(sub_result)
        for segment_group in self.find_segment_groups(lambda _: True):
            for sub_result in segment_group.get_all_value_pools():
                add_to_result(sub_result)
        return list(result)


def _replace_inputs_based_on_discriminator(
    segment_groups: List[SegmentGroup], replacement_func: Callable[[str], DeepAhbInputReplacement]
) -> None:
    """
    Replace all the entered_inputs in the entire list of segment groups using the given replacement_func.
    """
    for segment_group in segment_groups:
        if segment_group.segment_groups is not None:
            _replace_inputs_based_on_discriminator(segment_group.segment_groups, replacement_func)
        if segment_group.segments is None:
            continue
        for segment in segment_group.segments:
            for data_element in segment.data_elements:
                if isinstance(data_element, DataElementFreeText):
                    replacement_result = replacement_func(data_element.discriminator)
                    if replacement_result.replacement_found is True:
                        data_element.entered_input = replacement_result.input_replacement


class DeepAnwendungshandbuchSchema(Schema):
    """
    A schema to (de-)serialize :class:`.DeepAnwendungshandbuch`
    """

    meta = fields.Nested(AhbMetaInformationSchema)
    lines = fields.List(fields.Nested(SegmentGroupSchema))

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> DeepAnwendungshandbuch:
        """
        Converts the barely typed data dictionary into an actual :class:`.DeepAnwendungshandbuch`
        """
        return DeepAnwendungshandbuch(**data)
