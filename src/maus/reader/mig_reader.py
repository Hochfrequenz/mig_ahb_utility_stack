"""
Classes that allow to read XML files that contain structural information (Message Implementation Guide information)
"""
from abc import ABC, abstractmethod
from typing import Optional

from maus.models.edifact_components import EdifactStack
from maus.models.message_implementation_guide import SegmentGroupHierarchy
from maus.navigation import AhbLocation


class MigReader(ABC):
    """
    A MIG reader is a class that reads Message Implementation Guide (MIG) data from a source
    """

    @abstractmethod
    def to_segment_group_hierarchy(self) -> SegmentGroupHierarchy:
        """
        convert the read data into a segment group hierarchy
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")

    # pylint:disable=too-many-arguments
    @abstractmethod
    def get_edifact_stack(self, location: AhbLocation) -> Optional[EdifactStack]:
        """
        Returns the edifact stack for the given combination of segment group, key, data element and name
        """
        raise NotImplementedError("The inheriting class has to implement this method")
