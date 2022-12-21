# pylint:disable=too-few-public-methods
"""
Contains classes to Model Message Implementation Guides (MIG)
"""
from typing import List, Optional, Set, Tuple

import attrs
from marshmallow import Schema, fields, post_load

# pylint:disable=fixme
# TODO: the SegmentGroupHierarchy shall not be hardcoded but instead loaded from .tree files
# .tree files are a complete representation of an EDIFACT format including all segments and allowed data element values.
# A LARK grammar to parse them is work in progress at the moment and will be added later.
# From a parsed .tree file it is possible to also derive the segment group hierarchy.


@attrs.define(auto_attribs=True, kw_only=True, frozen=True)
class SegmentGroupHierarchy:
    """
    Models the hierarchy of segment groups within an EDIFACT format.
    Therefore each segment group is modeled together with its respective first segment inside the group.
    This is not a full representation of the EDIFACT formats structure but enough to understand the basic hierarchy.
    The Segment Group Hierarchy (SGH) is what allows us to transform a flat AHB into a NestedAhb that has a structure.
    This information / the SGH can be (manually) extracted form the diagrams in the MIG PDFs or generated from another
    source (which the BDEW does not provide, sadly).
    See the unit tests for working examples for UTILMD and MSCONS.
    It'll make sense then.
    """

    segment_group: Optional[str] = attrs.field(validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    """segment group name, e.g. "SG4" or "SG5" """
    opening_segment: str = attrs.field(validator=attrs.validators.instance_of(str))
    """first segment in group, e.g. 'IDE' or 'LOC' """
    sub_hierarchy: Optional[
        List["SegmentGroupHierarchy"]
    ]  #: segment groups below this level, e.g.[(SG5, LOG), (SG6,RFF), (SG8, SEQ), ...]

    def flattened(self) -> List[Tuple[Optional[str], str]]:
        """
        Returns the segment groups and opening tuples in the order in which they are expected to occur in an AHB.
        This is useful to match this deep structure with a flat AHB.
        """
        result: List[Tuple[Optional[str], str]] = [(self.segment_group, self.opening_segment)]
        if self.sub_hierarchy is not None:
            for sub_hier in self.sub_hierarchy:
                result += sub_hier.flattened()
        return result

    def is_hierarchically_below(self, segment_group_key: Optional[str]) -> bool:
        """
        returns true iff the segment_group provided is a (direct or indirect) sub group of self.
        """
        if self.sub_hierarchy is None:
            return False
        for sub_hier in self.sub_hierarchy:
            if sub_hier.segment_group == segment_group_key:
                return True
            if sub_hier.is_hierarchically_below(segment_group_key):
                return True
        return False

    def sg_is_hierarchically_below(
        self, segment_group_key_x: Optional[str], segment_group_key_y: Optional[str]
    ) -> bool:
        """
        returns true iff segment group with segment_group_key_x is hierarchically below the segment_group with key_y
        :param segment_group_key_x:
        :param segment_group_key_y:
        :return:
        """
        if segment_group_key_x == segment_group_key_y:
            return False
        if self.segment_group == segment_group_key_y:
            # because, if segment_group_x exists, it will be hierarchically below the root (y)
            all_sg_keys_in_this_sgh: Set[Optional[str]] = {x[0] for x in self.flattened()}
            if segment_group_key_x in all_sg_keys_in_this_sgh:
                return True
        for sub_hierarchy in self.sub_hierarchy or []:
            if sub_hierarchy.sg_is_hierarchically_below(segment_group_key_x, segment_group_key_y) is True:
                return True
        return False


class SegmentGroupHierarchySchema(Schema):
    """
    A schema to (de-)serialize :class:`.SegmentGroupHierarchy`
    """

    segment_group = fields.String(required=True, allow_none=True)
    opening_segment = fields.String(required=True)
    # disable unnecessary lambda warning because of circular imports
    sub_hierarchy = fields.List(
        fields.Nested(lambda: SegmentGroupHierarchySchema()), allow_none=True  # pylint:disable=unnecessary-lambda
    )

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> SegmentGroupHierarchy:
        """
        Converts the barely typed data dictionary into an actual :class:`.SegmentGroupHierarchy`
        """
        return SegmentGroupHierarchy(**data)
