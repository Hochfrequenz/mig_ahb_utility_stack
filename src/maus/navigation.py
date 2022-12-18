"""
the navigation module is contains models and code that allow to "navigate" through the AHB and MIG structure.
I.e. it allows to loop over an Anwendungshandbuch and "remember" which turns we took in the MIG structure (each turn is
a AhbLocationLayer) in order to arrive at a certain line of the AHB. This information is stored in an AhbLocation.
"""
import sys
from typing import Callable, List, Optional, Tuple, TypeVar

import attrs
from more_itertools import first_true, last

from maus import AhbLine, SegmentGroupHierarchy

T = TypeVar("T")


def _enhance_with_next_line_that_fulfills_predicate(
    ahb_lines: List[AhbLine], predicate: Callable[[AhbLine], bool], selector: Callable[[AhbLine], T]
) -> List[Tuple[AhbLine, Optional[T]]]:
    """
    For each line in ahb_line, find the next line that fulfills the predicate and return its property described by the
    selector.
    """
    # this function is not unit tested directly but only via _enhance_with_segment and _enhance_with_first_qualifier
    result: List[Tuple[AhbLine, Optional[T]]] = []
    for index, ahb_line in enumerate(ahb_lines):
        if predicate(ahb_line):
            result.append((ahb_line, selector(ahb_line)))
        else:
            first_line_that_matches_predicate = first_true(ahb_lines[index:], pred=predicate)
            if first_line_that_matches_predicate is None:
                break
            result.append((ahb_line, selector(first_line_that_matches_predicate)))
    ahb_line_index = len(result) - 1
    while len(result) < len(ahb_lines):
        result.append((ahb_lines[ahb_line_index], None))
        ahb_line_index += 1
    return result


def _enhance_with_next_segment(ahb_lines: List[AhbLine]) -> List[Tuple[AhbLine, str]]:
    """
    loop over the given ahb_lines, and return the same (unmodified) lines + the for each line the next segment code,
    which is not none. Here's an example:
    lines:
    [
    (line: Segment Group, Segment, Data Element)
    {SG1, None, None}
    {SG1, ABC, None}
    {SG1, ABC, 1234}
    {SG2, None, None}
    {SG2, DEF, None}
    {SG2, DEF, 5678}
    ]
    will return:
    [
    (line, str)
    {SG1, None, None}, ABC
    {SG1, ABC, None}, ABC
    {SG1, ABC, 1234}, ABC
    {SG2, None, None}, DEF
    {SG2, DEF, None}, DEF
    {SG2, DEF, 5678}, DEF
    ]
    """

    return _enhance_with_next_line_that_fulfills_predicate(
        ahb_lines=ahb_lines,
        predicate=lambda line: line.segment_code is not None,
        selector=lambda line: line.segment_code,  # type:ignore[return-value, arg-type]
        # predicate ensures that the selector does _not_ return None
    )


def _enhance_with_next_value_pool_entry(ahb_lines: List[AhbLine]) -> List[Tuple[AhbLine, str]]:
    """
    loop over the given ahb_lines, and return the same (unmodified) lines + the for each line the next value pool entry,
    which is not none. This is relevant to find the important first qualifier of the first segment in each segment group
    Here's an example:
    lines:
    [
    (line: Segment Group, Segment, Data Element, ValuePoolEntry)
    {SG1, ABC, None, None}
    {SG2, ABC, 1234, Z01}
    {SG2, DEF, None, None}
    {SG2, DEF, 5678, Z02}
    ]
    will return:
    [
    (line, str)
    {SG1, ABC, None, None}, Z01
    {SG1, ABC, 1234, Z01}, Z01
    {SG2, DEF, None, None}, Z02
    {SG2, DEF, 5678, Z02}, Z02
    ]
    """

    return _enhance_with_next_line_that_fulfills_predicate(
        ahb_lines=ahb_lines,
        predicate=lambda line: line.value_pool_entry is not None,
        selector=lambda line: line.value_pool_entry,  # type:ignore[return-value, arg-type]
        # predicate ensures that the selector does _not_ return None
    )


def _is_opening_segment_line_border(
    this_line: AhbLine, next_line: AhbLine, next_filled_segment: Optional[str], opening_segment_code: str
) -> bool:
    """
    returns true iff this_line and next_line are the border between two neighbouring segment groups with the same.
    This means that this_line is the last one in one segment group SGx and the next_line is in the first segment group
    SGx (note that both SGx are the same!)
    """
    # There are unit tests just for this method.
    # If you suspect the "group_by_segment_group" method to have a bug, check the tests for this method first.
    if this_line.section_name == next_line.section_name:
        # The first section of the next segment group (hopefully) never has the same section name as the last entry in
        # the previous group
        return False
    this_line_is_opening_segment = this_line.segment_code == opening_segment_code
    next_line_is_opening_segment = next_line == opening_segment_code
    this_line_has_empty_segment = this_line.segment_code is None
    if (
        (this_line_is_opening_segment is False)
        and (next_line_is_opening_segment is False)
        and (this_line_has_empty_segment is True)
    ):
        return False
    next_line_has_empty_segment = next_line.segment_code is None
    if next_line_is_opening_segment is False and next_line_has_empty_segment is False:
        return False
    return next_filled_segment == opening_segment_code


# pylint:disable=too-few-public-methods
@attrs.define(auto_attribs=True, kw_only=True, frozen=True)
class AhbLocationLayer:
    """
    The AhbLocation consists of multiple layers of information about the nesting of a line in the SegmentGroupHierarchy.
    one _AhbLocationLayer models exactly one of these nesting layers. It is used only internally in the AhbLocation.
    """

    segment_group_key: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.matches_re(r"^SG\d+$"))
    )
    """
    The key of the segment group in which the line is located; use None for the root.
    Example: "SG4"
    """
    opening_segment_code: str = attrs.field(validator=attrs.validators.matches_re(r"^[A-Z]{3}$"))
    """
    The opening_segment_code is the first segment code of the respective SegmentGroupHierarchy.
    Example: "IDE"
    """
    opening_qualifier: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.matches_re(r"^[A-Z]*\d*$"))
    )
    """"
    The opening_qualifier is the qualifier used in the opening_segment of this segment group.
    It is used to distinguish this segment group from other segment groups with the same key.
    (e.g. to distinguish between different SG8 for different purposes but the same internal structure).
    Example: "24"
    """


# pylint:disable=too-few-public-methods
@attrs.define(kw_only=True, auto_attribs=True, frozen=True)
class AhbLocation:
    """
    An ahb location describes where in a SegmentGroupHierarchy an AhbLine is located.
    The position is determined by the opening segments and qualifiers that have "passed by" while iterating over the
    lines inside an AHB from top to bottom.
    The location is initialized when you start iterating over the AHB by providing the relevant SegmentGroupHierarchy.
    Example: Consider the line: "SG10, CAV, 7111, Wertegranularität" from FV2210 UTILMD AHBs.
    It is located in
    * root (None, UNH, None)
    * "Vorgang" (SG4, IDE, 24)
    * "OBIS-Daten der Marktlokation" (SG8, SEQ, Z02)
    * "Wertegranularität" (SG10, CCI, ZE4)
    """

    layers: List[AhbLocationLayer] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(AhbLocationLayer),
            iterable_validator=attrs.validators.min_len(1),
        )
    )
    """
    the single layers that define the location
    """
    data_element_id: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.matches_re(r"^\d{4}$")), default=None
    )
    """
    the ID of th data element (inside the segment group described by layers), e.g. "0062"
    """
    qualifier: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(str)), default=None
    )
    """
    qualifier to identify the matching data element if the data_element id is not unique
    """


def determine_locations(
    segment_group_hierarchy: SegmentGroupHierarchy, ahb_lines: List[AhbLine]
) -> List[Tuple[AhbLine, AhbLocation]]:
    """
    If you provide _all_ lines of an AHB from top to bottom, this function will enrich the list of ahb_lines with the
    respective locations of the single AHBLines. These locations can then be used to find/match the lines with the MIG.
    :param segment_group_hierarchy: the general structure of the MIG
    :param ahb_lines: all lines of an AHB
    :return: the same lines that have been entered but together with their location which is derived from the segment
    group hierarchy.
    """
    starting_layer = AhbLocationLayer(
        segment_group_key=segment_group_hierarchy.segment_group,
        opening_segment_code=segment_group_hierarchy.opening_segment,
        opening_qualifier=None,
    )
    layers: List[AhbLocationLayer] = [starting_layer]
    # the layers are the internal representation of the position.
    # layers[0] is always the SGH root.
    # layers[-1] is the segment group that is also denoted at the beginning of the current AHBLine.

    # Basically we now iterate over the ahb_lines lines and try to remember which segment groups we entered on our
    # way and which one we also exited so that in the end, we know where the last item of ahb_lines is located.
    # To account reduce the complexity in this function, we first enhance the lines with additional information:
    # 1. what is the next segment code?
    # 2. what is the next qualifier?
    # Using these helper functions saves us from looking ahead in our iteration.
    # We only need to look at one item at a time
    current_sgh = segment_group_hierarchy
    parent_sgh: List[SegmentGroupHierarchy] = []
    result: List[Tuple[AhbLine, AhbLocation]] = []
    zip_kwars = {}
    if sys.version_info.minor >= 10:  # we implicitly assume python 3 here
        zip_kwars = {"strict": True}  # strict=True has been introduced in 3.10
    for this_ahb_line, this_next_segment, this_next_qualifier in list(
        zip(
            ahb_lines,
            [x[1] for x in _enhance_with_next_segment(ahb_lines)],
            [x[1] for x in _enhance_with_next_value_pool_entry(ahb_lines)],
            **zip_kwars
        )
    ):
        last_layer = last(layers)
        if this_ahb_line.segment_group_key == last_layer.segment_group_key:
            # todo: check for neighbouring segment group SGx->SGx
            # no segment group chance
            result.append((this_ahb_line, AhbLocation(layers=layers)))
            continue
        if (
            this_ahb_line.segment_group_key == last_layer.segment_group_key
            and this_next_qualifier != last_layer.opening_qualifier
        ):
            # switch to a neighbouring segment group (SGx->SGx) but with a different opening qualifier
            # parent stays the same (no pop to parent nor change of current sgh)
            layers.append(
                AhbLocationLayer(
                    segment_group_key=this_ahb_line.segment_group_key,
                    opening_segment_code=this_next_segment,
                    opening_qualifier=this_next_qualifier,
                )
            )
        else:
            # switch to a sublevel or to a neighbouring group with a different SG key (SGx->SGy)
            for sub_hierarchy in current_sgh.sub_hierarchy or []:
                if (
                    sub_hierarchy.segment_group == this_ahb_line.segment_group_key
                    and sub_hierarchy.opening_segment == (this_ahb_line.segment_code or this_next_segment)
                ):
                    break
            else:
                # We're sure that it's at least a step OUT, because it's an SG change and no suitable sub hierarchy was
                # found. The remaining question is: "How many segment groups did we leave at once?"
                layers.pop()  # this is the exit from the current group
                last_layer = last(layers)
                probably_current_sgh = parent_sgh[-1]
                if probably_current_sgh.segment_group != this_ahb_line.segment_group_key:
                    # we didn't move back to the parent but made a shortcut directly into the next (neighbouring)
                    # segment group.
                    layers.append(
                        AhbLocationLayer(
                            segment_group_key=this_ahb_line.segment_group_key,
                            opening_segment_code=this_next_segment,
                            opening_qualifier=this_next_qualifier,
                        )
                    )
                    # don't pop because the parent stays the same
                else:
                    current_sgh = parent_sgh.pop()
                    if (
                        last_layer.segment_group_key == this_ahb_line.segment_group_key
                        and last_layer.opening_qualifier != this_next_qualifier
                    ):
                        # remove the outdated SG with the same SG key (eg. in the SG2(MS)/SG3->SG2(MR) transition)
                        layers.pop()
                        layers.append(  # re-add it with the same SG x but a changed opening qualifier
                            AhbLocationLayer(
                                segment_group_key=this_ahb_line.segment_group_key,
                                opening_segment_code=this_next_segment,
                                opening_qualifier=this_next_qualifier,
                            )
                        )
                result.append((this_ahb_line, AhbLocation(layers=layers)))
                continue
            # now we're sure that it's a step _into_ a segment group because the step out runs into the for-else.
            layers.append(
                AhbLocationLayer(
                    segment_group_key=sub_hierarchy.segment_group,
                    opening_segment_code=sub_hierarchy.opening_segment,
                    opening_qualifier=this_next_qualifier,
                )
            )
            parent_sgh.append(current_sgh)
            current_sgh = sub_hierarchy
            assert current_sgh.segment_group == this_ahb_line.segment_group_key
        result.append((this_ahb_line, AhbLocation(layers=layers)))
    return result
