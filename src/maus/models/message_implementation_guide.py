# pylint:disable=too-few-public-methods
"""
Contains classes to Model Message Implementation Guides (MIG)
"""
from typing import List, Optional, Tuple

import attr
from marshmallow import Schema, fields, post_load


# pylint:disable=fixme
# TODO: the SegmentGroupHierarchy shall not be hardcoded but loaded from the .tree files
# I already wrote a LARK grammar that works for some trees but there's still some work left before we can use it here
# and derive the segment group hierarchy from it.


@attr.s(auto_attribs=True, kw_only=True)
class SegmentGroupHierarchy:
    """
    Models the hierarchy of segment groups within an EDIFACT format.
    This information can be (manually) extracted form the diagrams in the MIG PDF.
    """

    segment_group: Optional[str]  #: segment group name, f.e. "SG4" or "SG5"
    opening_segment: str  #: first segment in group, f.e. "IDE" or "LOC"
    sub_hierarchy: Optional[
        List["SegmentGroupHierarchy"]
    ]  #: segment groups below this level, f.e.[(SG5, LOG), (SG6,RFF), (SG8, SEQ), ...]

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

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> SegmentGroupHierarchy:
        """
        Converts the barely typed data dictionary into an actual :class:`.SegmentGroupHierarchy`
        """
        return SegmentGroupHierarchy(**data)
