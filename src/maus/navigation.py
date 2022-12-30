"""
the navigation module is contains models and code that allow to "navigate" through the AHB and MIG structure.
I.e. it allows to loop over an Anwendungshandbuch and "remember" which turns we took in the MIG structure (each turn is
a AhbLocationLayer) in order to arrive at a certain line of the AHB. This information is stored in an AhbLocation.
"""
import sys
from enum import Enum
from typing import Callable, List, Optional, Tuple, TypeVar, Union, overload

import attrs
from more_itertools import first_true, last

from maus.models.anwendungshandbuch import AhbLine
from maus.models.message_implementation_guide import SegmentGroupHierarchy

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
    the single layers that define the segment groups involved in the location
    """
    segment_code: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.matches_re(r"^[A-Z]{3}$")), default=None
    )
    """
    The segment code of an element. None for groups only.
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

    def is_sub_location_of(self, other: "AhbLocation") -> bool:
        """
        Returns true iff this (self) location is a sub position of the other provided location.
        ([Foo][0][Bar]).is_sub_position_of([Foo][0]) is true.
        """
        # this is kind of copied and pasted from EdifactStack.is_sub_stack_of
        # but any generalisation is probably not worth the loss of readability
        if len(other.layers) > len(self.layers):
            # self cannot be a sub path of other if other is "deeper"
            return False
        for layer_self, layer_other in zip(other.layers, self.layers):  # , strict=False):
            # strict is False because it's ok if we stop the iteration if self.levels is "exhausted"; explicit is better
            # the type-ignore for the strict=False is necessary for Python<3.10
            if layer_self != layer_other:
                return False
        # the iteration stopped meaning that for all layers that both other and self share, they are identical.
        # That's the definition of a sub location. It also means that any stack is a sub location of itself.
        return True

    def is_parent_of(self, other: "AhbLocation") -> bool:
        """
        Returns true iff this other stack is a sub position of self.
        """
        return other.is_sub_location_of(self)


@attrs.define(kw_only=True, frozen=True, auto_attribs=True)
class _PseudoAhbLocation(AhbLocation):
    """
    a separate class to distinguish _real_ ahb locations from fake/pseudo ahb locations.
    The latter should never be used outside this module.
    """


@overload
def find_common_ancestor(location_x: _PseudoAhbLocation, location_y: _PseudoAhbLocation) -> _PseudoAhbLocation:
    ...


@overload
def find_common_ancestor(
    location_x: _PseudoAhbLocation, location_y: Union[AhbLocation, _PseudoAhbLocation]
) -> _PseudoAhbLocation:
    ...


@overload
def find_common_ancestor(
    location_x: Union[AhbLocation, _PseudoAhbLocation], location_y: _PseudoAhbLocation
) -> _PseudoAhbLocation:
    ...


@overload
def find_common_ancestor(location_x: AhbLocation, location_y: AhbLocation) -> AhbLocation:
    ...


def find_common_ancestor(
    location_x: Union[AhbLocation, _PseudoAhbLocation], location_y: Union[AhbLocation, _PseudoAhbLocation]
) -> Union[AhbLocation, _PseudoAhbLocation]:
    """
    Finds the last common ancestor of location_x and location_y.
    If the layers of location X are:  [A,B,C,F,G,H]
    And the layers of location Y are: [A,B,C,D,E,F]
    then the last common ancestor is: [A,B,C]
    :param location_x:
    :param location_y:
    :return: the location that is the last common ancestor of x and y
    """
    result_layers: List[AhbLocationLayer] = []
    only_consider_sg_key = isinstance(location_x, _PseudoAhbLocation) or isinstance(location_y, _PseudoAhbLocation)
    for layer_x, layer_y in zip(location_x.layers, location_y.layers):
        if layer_x == layer_y or (
            only_consider_sg_key is True and layer_x.segment_group_key == layer_y.segment_group_key
        ):
            result_layers.append(layer_x)
        else:
            break
    try:
        if only_consider_sg_key:
            return _PseudoAhbLocation(layers=result_layers)
        return AhbLocation(layers=result_layers)
    except ValueError as value_error:
        # We raise an exception if len(result_layers) is 0 because this case shouldn't happen in locations that
        # originate from the same AHB.
        raise ValueError("There is no common ancestor") from value_error


def _construct_pseudo_location(
    sg_key: Optional[str],
    segment_group_hierarchy: SegmentGroupHierarchy,
    existing_layers: Optional[List[AhbLocationLayer]] = None,
) -> Optional[_PseudoAhbLocation]:
    """
    use the segment group hierarchy to _guess_ where the segment group with key sg_key is located
    :param sg_key:
    :param segment_group_hierarchy:
    :return:
    """
    this_layer = AhbLocationLayer(
        segment_group_key=segment_group_hierarchy.segment_group,
        opening_segment_code=segment_group_hierarchy.opening_segment,
        opening_qualifier=None,
    )
    layers: List[AhbLocationLayer]
    if existing_layers is None:
        layers = [this_layer]
    else:
        layers = existing_layers.copy()
        layers.append(this_layer)
    if sg_key == segment_group_hierarchy.segment_group:
        return _PseudoAhbLocation(layers=layers)
    for sub_hierarchy in segment_group_hierarchy.sub_hierarchy or []:
        sub_result = _construct_pseudo_location(sg_key, sub_hierarchy, layers)
        if sub_result is not None:
            return sub_result
    return None


def _find_common_ancestor_from_sgh(
    sg_key_x: Optional[str], sg_key_y: Optional[str], segment_group_hierarchy: SegmentGroupHierarchy
) -> _PseudoAhbLocation:
    """
    Finds the last common ancestor of the segment groups x and y.
    The function uses the provided segment group hierarchy to construct pseudo AHBLocations.
    These locations are then fed into the other overload of find_common_ancestor
    :param segment_group_hierarchy: the SGH used to locate the SGs
    :param sg_key_x: key of the segment group at location x
    :param sg_key_y: key of the segment group at location y
    :return: A Pseudo-Location that is a placeholder for the last common ancestor of x and y
    """
    location_x: Optional[_PseudoAhbLocation] = _construct_pseudo_location(sg_key_x, segment_group_hierarchy)
    if location_x is None:
        raise ValueError(f"Couldn't locate {sg_key_x} in the given hierarchy")
    location_y: Optional[_PseudoAhbLocation] = _construct_pseudo_location(sg_key_y, segment_group_hierarchy)
    if location_x is None:
        raise ValueError(f"Couldn't locate {sg_key_y} in the given hierarchy")
    # note that the result is generally complete. just the number of layers has a meaning
    return find_common_ancestor(location_x, location_y)  # type:ignore[arg-type]


@attrs.define(auto_attribs=True, frozen=True, kw_only=True)
class _AhbLocationDistance:
    """
    Describes the differences in the hierarchy between two locations.
    Assume the start location is layers=[A,B,C,D,E,F] and the target location is layers=[A,B,G,H].
    Then the distance is (with B as common ancestor):
    layers_up = 4 (F--1-->E--2-->D--3-->C--4-->B)
    layers_down = 2 (B--1-->G--2-->H)
    A distance with layers_down == layers_up == 1 means the two locations are sibling.
    A distance with layers_down == 0 means that the target location is a parent of the source location.
    A distance with layers_up == 0 means that the source location is a parent of the target location.
    """

    layers_up: int = attrs.field(
        validator=attrs.validators.and_(attrs.validators.instance_of(int), attrs.validators.ge(0))
    )
    """
    Describes the number of layers (up) between the source location and the common ancestor of both locations.
    Is always >= 0.
    """
    layers_down: int = attrs.field(
        validator=attrs.validators.and_(attrs.validators.instance_of(int), attrs.validators.ge(0))
    )
    """
    Describes the number of layer (down) between the common ancestor of both locations and the target location.
    Is always >= 0.
    """


def calculate_distance(location_x: AhbLocation, location_y: AhbLocation) -> _AhbLocationDistance:
    """
    Calculate the "distance" between two locations.
    The distance is measured in how many layers you have to go up and how many down reach location_y from location_y.
    For more information see the docstring of `_AhbLocationDistance`
    :param location_x: the start location
    :param location_y: the target location
    :return: the number of layers between location_x and location_y via their common ancestor.
    """
    common_ancestor = find_common_ancestor(location_x, location_y)
    return _AhbLocationDistance(
        layers_up=len(location_x.layers) - len(common_ancestor.layers),
        layers_down=len(location_y.layers) - len(common_ancestor.layers),
    )


class _DifferentialAhbLineHierarchyChange(Enum):
    """
    Describes the different scenarios that can happen when moving from one AHBline to the next.
    """

    STAY = 1  #: Stay in the same ("selbe") segment group; e.g. UTILMD SG4 IDE+24 -> SG4 IDE+24
    MOVE_TO_NEIGHBOUR_SAME_KEY = 2
    """
    Stay on the same hierarchy level but move to a neighbouring group that has the same segment group key.
    E.g. UTILMD SG2 NAD+MS -> SG2 NAD+MR
    """
    MOVE_TO_NEIGHBOUR_DIFFERENT_KEY = 4
    """
    Stay on the same hierarchy level but move to a neighbouring group with a different segment group key.
    E.g. UTILMD SG5 LOC -> SG6 RFF
    """
    DIVE_INTO_SUB_GROUP = 8
    """
    Move into a nested subgroup with a different segment group key.
    E.g. UTILMD SG2->SG3
    """
    LEAVE_TO_PARENT = 16
    """
    Leave a segment group back to the parent hierarchy level. E.g. UTILMD SG3 -> SG2
    """
    LEAVE_TO_PARENT_AND_DIVE_INTO_SUB_GROUP = DIVE_INTO_SUB_GROUP + LEAVE_TO_PARENT
    """
    often when leaving one sub group we directly dive into the next one.
    """

    def is_segment_group_change(self) -> bool:
        """
        returns true iff this item is denotes any segment groups change
        """
        return self != _DifferentialAhbLineHierarchyChange.STAY


def _this_line_is_hierarchically_below_the_previous_sg_key(
    this_line: AhbLine, previous_segment_group_key, segment_group_hierarchy: SegmentGroupHierarchy
) -> bool:
    """
    returns true iff this_line is hierarchically below the previous segment group key; false otherwise
    :param this_line: e.g. SG3 CTA
    :param previous_segment_group_key: SG2
    :param segment_group_hierarchy: [UNH, [SG2 [SG3]], [SG2], [SG4[SG...]]]
    :return: true if SG3 hierarchically line is below SG2
    """
    if this_line.segment_group_key == previous_segment_group_key:
        return False
    if segment_group_hierarchy.segment_group == previous_segment_group_key:
        # anything is below root
        return True
    return segment_group_hierarchy.sg_is_hierarchically_below(this_line.segment_group_key, previous_segment_group_key)


# pylint:disable=too-many-arguments
def _determine_hierarchy_change(
    this_ahb_line: AhbLine,
    previous_ahb_line: Optional[AhbLine],
    this_next_segment: str,
    this_next_qualifier: str,
    last_opening_segment: Optional[str],
    last_opening_qualifier: Optional[str],
    is_ready_for_sg_change: bool,
    segment_group_hierarchy: SegmentGroupHierarchy,
) -> _DifferentialAhbLineHierarchyChange:
    """
    Determine which kind of transition happens between two AHB lines
    :return: see `_DifferentialAhbLineHierarchyChange`
    """
    previous_sg_key: Optional[str] = None
    if previous_ahb_line is not None:
        previous_sg_key = previous_ahb_line.segment_group_key
    if this_ahb_line.segment_group_key == previous_sg_key:  # No segment group change (key);
        if this_next_segment != last_opening_segment:
            return _DifferentialAhbLineHierarchyChange.STAY
        # next segment opens a new group with the same key
        if this_next_qualifier == last_opening_qualifier or (
            # as long as we're in UNH, we stay in UNH
            last_opening_segment is None
            and this_next_segment == "UNH"
        ):
            return _DifferentialAhbLineHierarchyChange.STAY
        if is_ready_for_sg_change:
            return _DifferentialAhbLineHierarchyChange.MOVE_TO_NEIGHBOUR_SAME_KEY
        return _DifferentialAhbLineHierarchyChange.STAY

    # An SG (key) change happened. Now we have to distinguish. Did we switch...
    # * ...to a sub group nested inside (add layers)
    # * ...back to a parent group (remove layers)
    # * ...even both: move to parent (remove layer) and then dive into another subgroup (add layer) at the same time
    if segment_group_hierarchy.sg_is_hierarchically_below(this_ahb_line.segment_group_key, previous_sg_key):
        return _DifferentialAhbLineHierarchyChange.DIVE_INTO_SUB_GROUP
    if segment_group_hierarchy.sg_is_hierarchically_below(previous_sg_key, this_ahb_line.segment_group_key):
        # result = _DifferentialAhbLineHierarchyChange.LEAVE_TO_PARENT
        # let's check if we're back in the previous parent sg or already in another sub sg
        # we'd detect that we move into the next subgroup already
        # todo: does the case leave to parent really happen? maybe for unh only?
        pass
    return _DifferentialAhbLineHierarchyChange.LEAVE_TO_PARENT_AND_DIVE_INTO_SUB_GROUP  # sibling A->B->C to A-B->D


def determine_hierarchy_changes(
    ahb_lines: List[AhbLine], segment_group_hierarchy: SegmentGroupHierarchy
) -> List[Tuple[AhbLine, _DifferentialAhbLineHierarchyChange]]:
    """
    Determine the differential hierarchy changes between neighbouring ahb lines.
    The returned tuple at index n is the line n itself + the change in hierarchy necessary to get from line n-1 to n.
    """
    result: List[Tuple[AhbLine, _DifferentialAhbLineHierarchyChange]] = []
    segment_code_was_none = True
    previous_line: Optional[AhbLine] = None
    last_opening_qualifier: str = "UNH"
    last_opening_segment: Optional[str] = None
    zip_kwargs = {}
    if sys.version_info.minor >= 10:  # we implicitly assume python 3 here
        zip_kwargs = {"strict": True}  # strict=True has been introduced in 3.10
    for this_ahb_line, this_next_segment, this_next_qualifier in list(
        zip(
            ahb_lines,
            [x[1] for x in _enhance_with_next_segment(ahb_lines)],
            [x[1] for x in _enhance_with_next_value_pool_entry(ahb_lines)],
            **zip_kwargs,
        )
    ):

        if this_ahb_line.segment_code is None:
            segment_code_was_none = True
        change = _determine_hierarchy_change(
            this_ahb_line=this_ahb_line,
            previous_ahb_line=previous_line,
            this_next_segment=this_next_segment,
            this_next_qualifier=this_next_qualifier,
            last_opening_qualifier=last_opening_qualifier,
            last_opening_segment=last_opening_segment,
            is_ready_for_sg_change=segment_code_was_none,
            segment_group_hierarchy=segment_group_hierarchy,
        )
        if change.is_segment_group_change():
            last_opening_qualifier = this_next_qualifier
            last_opening_segment = this_next_segment
        if this_ahb_line.segment_code is not None:
            segment_code_was_none = False
        result.append((this_ahb_line, change))
        previous_line = this_ahb_line
    return result


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
    result: List[Tuple[AhbLine, AhbLocation]] = []
    for (this_ahb_line, change), this_next_segment, this_next_qualifier in zip(
        determine_hierarchy_changes(ahb_lines, segment_group_hierarchy),
        [x[1] for x in _enhance_with_next_segment(ahb_lines)],
        [x[1] for x in _enhance_with_next_value_pool_entry(ahb_lines)],
    ):
        if last(layers).opening_qualifier is None and len(result) == 0:
            layers[-1] = AhbLocationLayer(
                segment_group_key=segment_group_hierarchy.segment_group,
                opening_segment_code=segment_group_hierarchy.opening_segment,
                opening_qualifier=this_next_qualifier,
            )
        if change == _DifferentialAhbLineHierarchyChange.STAY:
            # No segment group change; The layers represent the location already.
            result.append(
                (
                    this_ahb_line,
                    AhbLocation(
                        layers=layers.copy(), data_element_id=this_ahb_line.data_element, segment_code=this_next_segment
                    ),
                )
            )
            continue
        if change == _DifferentialAhbLineHierarchyChange.MOVE_TO_NEIGHBOUR_SAME_KEY:
            layers.pop()
            layers.append(
                AhbLocationLayer(
                    segment_group_key=this_ahb_line.segment_group_key,
                    opening_segment_code=this_next_segment,
                    opening_qualifier=this_next_qualifier,
                )
            )
            result.append(
                (
                    this_ahb_line,
                    AhbLocation(
                        layers=layers.copy(), data_element_id=this_ahb_line.data_element, segment_code=this_next_segment
                    ),
                )
            )
            continue
        # switch to a sublevel or to a neighbouring group with a different SG key (SGx->SGy)
        if change == _DifferentialAhbLineHierarchyChange.DIVE_INTO_SUB_GROUP:
            # we moved into a subgroup, e.g. from UTILMD SG4 to SG5
            layers.append(
                AhbLocationLayer(
                    segment_group_key=this_ahb_line.segment_group_key,
                    opening_segment_code=this_next_segment,
                    opening_qualifier=this_next_qualifier,
                )
            )
            result.append(
                (
                    this_ahb_line,
                    AhbLocation(
                        layers=layers.copy(), data_element_id=this_ahb_line.data_element, segment_code=this_next_segment
                    ),
                )
            )
            continue
        if change == _DifferentialAhbLineHierarchyChange.LEAVE_TO_PARENT_AND_DIVE_INTO_SUB_GROUP:
            # [SG2 (NAD+MS), SG3]->[SG2 (NAD+MR)] # one group up (leave SG3, then remove old SG2)
            # [SG4, SG8, SG10]-> [SG4,SG12] # two groups up! (leave SG10, leave SG8, then enter sg12)
            common_ancestor = _find_common_ancestor_from_sgh(
                last(last(result)[1].layers).segment_group_key, this_ahb_line.segment_group_key, segment_group_hierarchy
            )
            distance_to_common_ancestor = calculate_distance(last(result)[1], common_ancestor)
            for _ in range(0, distance_to_common_ancestor.layers_up):
                # actually: this should be a separate case in the differential change enum
                layers.pop()
                if last(layers).segment_group_key == this_ahb_line.segment_group_key:  # this removes the old SG2
                    layers.pop()
            layers.append(  # this adds the next SG2
                AhbLocationLayer(
                    segment_group_key=this_ahb_line.segment_group_key,
                    opening_segment_code=this_next_segment,
                    opening_qualifier=this_next_qualifier,
                )
            )
            result.append(
                (
                    this_ahb_line,
                    AhbLocation(
                        layers=layers.copy(), data_element_id=this_ahb_line.data_element, segment_code=this_next_segment
                    ),
                )
            )
            continue
        if change == _DifferentialAhbLineHierarchyChange.LEAVE_TO_PARENT:
            raise NotImplementedError("todo think if this really happens")
    return result
