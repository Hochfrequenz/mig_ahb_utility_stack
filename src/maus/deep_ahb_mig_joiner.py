"""
A module to mix/join information from the deep ahb and the MIG (beyond SGH)
"""
from typing import Dict, List, Optional, Tuple

from maus import DataElementFreeText, DataElementValuePool, DeepAnwendungshandbuch
from maus.edifact import is_edifact_boilerplate
from maus.models.edifact_components import (
    DataElement,
    EdifactStack,
    EdifactStackQuery,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)
from maus.reader.mig_reader import MigReader


# pylint:disable=too-many-branches
def _replace_discriminators_with_edifact_stack_segments(
    segments: List[Segment],
    segment_group_key: str,
    mig_reader: MigReader,
    # the fallback_predecessors are kind of a "overflow" / "Übertrag" from parent segment groups
    # without the fallback_predecessors the single segment groups would be handled independently of each other,
    # which is great for readability, debuggability and testing
    # but sadly the complexity of the AHBs requires a coupling.
    fallback_predecessors: Dict[str, List[str]],
    ignore_errors: bool = False,
) -> Tuple[List[Segment], Dict[str, List[str]]]:
    result = segments.copy()
    predecessors_used: Dict[str, List[str]] = {}  # maps the segment code to a set of qualifiers used as predecessors
    predecessor_qualifier: Optional[str] = None
    # pylint:disable=too-many-nested-blocks
    for segment_index, segment in enumerate(
        s for s in segments if not is_edifact_boilerplate(s.discriminator)
    ):  # type:ignore[union-attr]
        previous_predecessor_qualifier: Optional[str] = predecessor_qualifier or None
        predecessor_qualifier = None
        for de_index, data_element in enumerate(segment.data_elements):
            if isinstance(data_element, DataElementFreeText):
                stack = _handle_free_text(mig_reader, segment_group_key, segment, data_element, predecessor_qualifier)
                # for easy error analysis set a conditional break point here for 'stack is None'
                if stack is not None:
                    result[segment_index].data_elements[de_index].discriminator = stack.to_json_path()
                elif ignore_errors:
                    raise ValueError(f"Couldn't find a stack for (DataElementFreeText {data_element})")
            if isinstance(data_element, DataElementValuePool):
                stack = _handle_value_pool(
                    mig_reader, segment_group_key, segment, data_element, predecessor_qualifier, fallback_predecessors
                )
                if stack is not None:
                    result[segment_index].data_elements[de_index].discriminator = stack.to_json_path()
                elif len(data_element.value_pool) > 1:
                    if previous_predecessor_qualifier is not None:
                        stack = _handle_value_pool(
                            mig_reader,
                            segment_group_key,
                            segment,
                            data_element,
                            previous_predecessor_qualifier,
                            fallback_predecessors,
                        )
                        if stack is not None:
                            result[segment_index].data_elements[de_index].discriminator = stack.to_json_path()
                    if stack is None and not ignore_errors and not _data_element_has_a_known_problem(data_element):
                        raise ValueError(
                            f"Any value pool with more than 1 entry has to have an edifact stack {data_element}"
                        )
                if len(data_element.value_pool) == 1:
                    predecessor_qualifier = data_element.value_pool[0].qualifier
                    try:
                        predecessors_used[segment.discriminator].append(predecessor_qualifier)
                    except KeyError:
                        predecessors_used[segment.discriminator] = [predecessor_qualifier]
                else:
                    predecessor_qualifier = None
    return result, predecessors_used


def _data_element_has_a_known_problem(data_element: DataElement):
    if data_element.discriminator == "SG10->CAV->7110":
        # https://github.com/Hochfrequenz/edifact-templates/issues/59
        return True
    if data_element.discriminator == "SG10->CCI->7037":
        # https://github.com/Hochfrequenz/edifact-templates/issues/60
        return True
    if data_element.discriminator == "SG6->DTM->2379":
        # https://github.com/Hochfrequenz/edifact-templates/issues/63
        return True
    if data_element == DataElementValuePool(
        discriminator="SG8->RFF->1153",
        data_element_id="1153",
        value_pool=[
            ValuePoolEntry(qualifier="MG", meaning="Gerätenummer des Zählers", ahb_expression="X"),
            ValuePoolEntry(qualifier="Z11", meaning="Gerätenummer des Mengenumwerters", ahb_expression="X"),
            ValuePoolEntry(qualifier="Z14", meaning="Smartmeter-Gateway", ahb_expression="X"),
        ],
    ):
        # https://github.com/Hochfrequenz/edifact-templates/issues/65
        return True
    if data_element == DataElementValuePool(
        discriminator="SG4->DTM->2005",
        data_element_id="2005",
        value_pool=[
            ValuePoolEntry(qualifier="Z05", meaning="gegenüber Kunde bestätigtes Kündigungsdatum", ahb_expression="X"),
            ValuePoolEntry(
                qualifier="Z06", meaning="gegenüber Lieferant bestätigtes Kündigungsdatum", ahb_expression="X"
            ),
        ],
    ):
        # https://github.com/Hochfrequenz/edifact-templates/issues/69
        return True
    return False


def _handle_free_text(
    mig_reader: MigReader,
    segment_group_key: str,
    segment: Segment,
    data_element: DataElementFreeText,
    predecessor_qualifier: Optional[str],
) -> Optional[EdifactStack]:
    query = EdifactStackQuery(
        segment_group_key=segment_group_key,
        segment_code=segment.discriminator,
        data_element_id=data_element.data_element_id,
        name=data_element.discriminator,
        predecessor_qualifier=predecessor_qualifier,
        section_name=segment.section_name,
    )
    stack = mig_reader.get_edifact_stack(query)
    return stack


# todo: fix this later
# pylint:disable=too-many-arguments
def _handle_value_pool(
    mig_reader: MigReader,
    segment_group_key: str,
    segment: Segment,
    data_element: DataElementValuePool,
    predecessor_qualifier: Optional[str],
    fallback_predecessors: Dict[str, List[str]],
) -> Optional[EdifactStack]:
    query = EdifactStackQuery(
        segment_group_key=segment_group_key,
        segment_code=segment.discriminator,
        data_element_id=data_element.data_element_id,
        name=None,
        predecessor_qualifier=predecessor_qualifier,
        section_name=segment.section_name,
    )
    stack = mig_reader.get_edifact_stack(query)
    if stack is not None:
        return stack
    if len(data_element.value_pool) > 1:
        stack = _find_stack_using_fallback_predecessors(
            mig_reader, query_draft=query, fallback_predecessors=fallback_predecessors
        )
        if stack is not None:
            return stack
    return None


def _find_stack_using_fallback_predecessors(
    mig_reader: MigReader, query_draft: EdifactStackQuery, fallback_predecessors: Dict[str, List[str]]
) -> Optional[EdifactStack]:
    all_fallback_predecessors: List[str] = []
    for predecessor_list in fallback_predecessors.values():
        # The predecessors are added to this list in the order in which they occur in the AHB.
        # My _guess_ (and only a guess) is, that the reversed order has better matches.
        # This (in UTILMD) particularly affects ( https://github.com/Hochfrequenz/edifact-templates/pull/84/files )
        # - Lastprofildaten (Gas)/(Strom) vs. Profilschardaten
        # - Konzessionsabgaben vs. Zuordnung Konzessionsabgaben
        # - Kommunikationseinrichtung vs. Technische Steuereinrichtung vs. Steuer-/Abgabeninformation vs. Wandlerdaten
        # We need to find out.
        for value in reversed(predecessor_list):
            all_fallback_predecessors.append(value)
    for fallback_predecessor in all_fallback_predecessors:
        query = EdifactStackQuery(
            segment_group_key=query_draft.segment_group_key,
            segment_code=query_draft.segment_code,
            data_element_id=query_draft.data_element_id,
            name=query_draft.name,
            section_name=query_draft.section_name,
            predecessor_qualifier=fallback_predecessor,
        )
        query.predecessor_qualifier = fallback_predecessor
        edifact_stack = mig_reader.get_edifact_stack(query)
        if edifact_stack is not None:
            return edifact_stack
    return None


def _replace_discriminators_with_edifact_stack_groups(
    segment_groups: List[SegmentGroup],
    mig_reader: MigReader,
    fallback_predecessors: Dict[str, List[str]],
    ignore_errors: bool = False,
) -> List[SegmentGroup]:
    """
    replaces all discriminators in the given list of segment groups with an edifact seed path from the provided reader
    """
    result = segment_groups.copy()
    for segment_group_index, segment_group in enumerate(segment_groups):
        current_segment_group_key = segment_group.discriminator
        if result[segment_group_index].segments is not None:
            segments_result, predecessor_qualifiers_used = _replace_discriminators_with_edifact_stack_segments(
                segments=result[segment_group_index].segments,  # type:ignore[arg-type]
                segment_group_key=current_segment_group_key,
                mig_reader=mig_reader,
                ignore_errors=ignore_errors,
                fallback_predecessors=fallback_predecessors,
            )
            result[segment_group_index].segments = segments_result
        if result[segment_group_index].segment_groups is not None:
            result[segment_group_index].segment_groups = _replace_discriminators_with_edifact_stack_groups(
                segment_groups=segment_group.segment_groups,  # type:ignore[arg-type]
                mig_reader=mig_reader,
                ignore_errors=ignore_errors,
                fallback_predecessors=predecessor_qualifiers_used,
            )
    return result


def replace_discriminators_with_edifact_stack(
    deep_ahb: DeepAnwendungshandbuch, mig_reader: MigReader, ignore_errors: bool = False
) -> None:
    """
    replaces all discriminators in deep_ahb with an edifact seed path from the provided mig_reader
    """
    deep_ahb.lines = _replace_discriminators_with_edifact_stack_groups(
        deep_ahb.lines, mig_reader, fallback_predecessors={}, ignore_errors=ignore_errors
    )
