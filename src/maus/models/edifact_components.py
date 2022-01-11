# pylint:disable=too-few-public-methods
"""
EDIFACT components are data structures on different hierarchical levels inside an EDIFACT message.
Components contain not only EDIFACT composits but also segments and segment groups.
"""
from abc import ABC
from typing import Dict, List, Optional, Type

import attr
from marshmallow import Schema, fields, post_dump, post_load, pre_dump, pre_load  # type:ignore[import]


@attr.s(auto_attribs=True, kw_only=True)
class DataElement(ABC):
    """
    A data element holds specific kinds of data. It is defined in EDIFACT.
    At least for the German energy market communication any data element has a 4 digit key.
    For example in UTILMD the data element that holds the 13 digit market partner ID is data element '3039'
    """

    discriminator: str = attr.ib(validator=attr.validators.instance_of(str))
    """ The discriminator uniquely identifies the data element. This _might_ be its key """
    # but could also be a reference or a name


class DataElementSchema(Schema):
    """
    A Schema to (de-)serialize DataElements
    """

    discriminator = fields.String(required=True)


@attr.s(auto_attribs=True, kw_only=True)
class DataElementFreeText(DataElement):
    """
    A DataElementFreeText is a data element that allows entering arbitrary data.
    This is the main difference to the :class:`DataElementValuePool` which has a finite set of allowed values attached.
    """

    ahb_expression: str = attr.ib(validator=attr.validators.instance_of(str))
    """any freetext data element has an ahb expression attached. Could be 'X' but also 'M [13]'"""
    entered_input: Optional[str] = attr.ib(validator=attr.validators.optional(attr.validators.instance_of(str)))
    """If the message contains data for this data element, this is not None."""


class DataElementFreeTextSchema(DataElementSchema):
    """
    A Schema to serialize DataElementFreeTexts
    """

    ahb_expression = fields.String(required=True)
    entered_input = fields.String(required=False, load_default=None)

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> DataElementFreeText:
        """
        Converts the barely typed data dictionary into an actual :class:`.DataElementFreeText`
        """
        return DataElementFreeText(**data)


@attr.s(auto_attribs=True, kw_only=True)
class DataElementValuePool(DataElement):
    """
    A DataElementValuePool is a data element with a finite set of allowed values.
    These allowed values are referred to as keys of the "value pool".
    The value pool is defined both on MIG level and AHB level
    The set of values allowed according to the AHB is always a subset of the values allowed according to the MIG.
    """

    value_pool: Dict[str, str]  #: The value pool contains the allowed values as key and their meaning as value.
    # for example data element 3055 in UTILMD (used in NAD+MR and NAD+MS) has the value pool:
    # { "9": "GS1", "293": "DE, BDEW", "332": "DE, DVGW" }


class DataElementValuePoolSchema(DataElementSchema):
    """
    A Schema to serialize DataElementValuePool
    """

    value_pool = fields.Dict(keys=fields.String(required=True), values=fields.String(required=True), required=True)

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> DataElementValuePool:
        """
        Converts the barely typed data dictionary into an actual :class:`.DataElementValuePool`
        """
        return DataElementValuePool(**data)


class _FreeTextOrValuePool:
    """
    A class that is easily serializable as dictionary and allows us to _not_ use the marshmallow-union package.
    """

    def __init__(
        self, free_text: Optional[DataElementFreeText] = None, value_pool: Optional[DataElementValuePool] = None
    ):
        self.free_text = free_text
        self.value_pool = value_pool

    free_text: Optional[DataElementFreeText] = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(DataElementFreeText))
    )
    value_pool: Optional[DataElementValuePool] = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(DataElementValuePool))
    )


class _FreeTextOrValuePoolSchema(Schema):
    """
    A schema that represents data of the kind Union[DataElementFreeText,DataElementValuePool]
    There is a python package for that: https://github.com/adamboche/python-marshmallow-union
    but is only has 15 stars; not sure if it's worth the dependency
    """

    # disable unnecessary lambda warning because of circular imports
    free_text = fields.Nested(
        lambda: DataElementFreeTextSchema(), allow_none=True, required=False  # pylint: disable=unnecessary-lambda
    )  # fields.String(dump_default=False, required=False, allow_none=True)
    value_pool = fields.Nested(
        lambda: DataElementValuePoolSchema(), required=False, allow_none=True  # pylint: disable=unnecessary-lambda
    )

    # pylint:disable= unused-argument, no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> Type[DataElement]:
        """
        select the correct part of the data to deserialize
        """
        if "free_text" in data and data["free_text"]:
            return data["free_text"]
        if "value_pool" in data and data["value_pool"]:
            return data["value_pool"]
        return data

    # pylint:disable= unused-argument, no-self-use
    @post_dump
    def post_dump_helper(self, data, **kwargs) -> dict:
        """
        truncate the part _FreeTextOrValuePool that is not needed
        """
        if "value_pool" in data and data["value_pool"]:
            return data["value_pool"]
        if "free_text" in data and data["free_text"]:
            return data["free_text"]
        raise NotImplementedError(f"Data {data} is not implemented for JSON serialization")

    # pylint:disable= unused-argument, no-self-use
    @pre_load
    def pre_load_helper(self, data, **kwargs) -> dict:
        """
        Put the untyped data into a structure that is deserializable as _FreeTextOrValuePool
        """
        if "value_pool" in data:
            return {
                "free_text": None,
                "value_pool": data,
            }
        if "entered_input" in data:
            return {
                "free_text": data,
                "value_pool": None,
            }
        raise NotImplementedError(f"Data {data} is not implemented for JSON deserialization")

    # pylint:disable= unused-argument, no-self-use
    @pre_dump
    def prepare_for_serialization(self, data, **kwargs) -> _FreeTextOrValuePool:
        """
        Detect if data are FreeText or ValuePool data elements
        """
        if isinstance(data, DataElementValuePool):
            return _FreeTextOrValuePool(free_text=None, value_pool=data)
        if isinstance(data, DataElementFreeText):
            return _FreeTextOrValuePool(free_text=data, value_pool=None)
        raise NotImplementedError(f"Data type of {data} is not implemented for JSON serialization")


@attr.s(auto_attribs=True, kw_only=True)
class SegmentLevel(ABC):
    """
    SegmentLevel describes @annika: what does it describe?
    """

    discriminator: str
    ahb_expression: str


class SegmentLevelSchema(Schema):
    """
    A Schema to serialize SegmentLevels
    """

    discriminator = fields.String(required=True)
    ahb_expression = fields.String(required=True)


@attr.s(auto_attribs=True, kw_only=True)
class Segment(SegmentLevel):
    """
    A Segment contains multiple data elements.
    """

    data_elements: List[DataElement]


class SegmentSchema(SegmentLevelSchema):
    """
    A Schema to serialize Segments.
    """

    data_elements = fields.List(fields.Nested(_FreeTextOrValuePoolSchema))

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> Segment:
        """
        Converts the barely typed data dictionary into an actual :class:`.Segment`
        """
        return Segment(**data)


@attr.s(auto_attribs=True, kw_only=True)
class SegmentGroup(SegmentLevel):
    """
    A segment group that contains segments and nested groups.
    On root level of a message there might be a "virtual" segment group of all segments that formally don't have a group
    This group has the key "root".
    """

    segments: Optional[List[Segment]] = attr.ib(
        validator=attr.validators.optional(
            attr.validators.deep_iterable(
                member_validator=attr.validators.instance_of(Segment),
                iterable_validator=attr.validators.instance_of(list),
            )
        )
    )  #: the segments inside this very group
    segment_groups: Optional[List["SegmentGroup"]]  #: groups that are nested into this group


class SegmentGroupSchema(SegmentLevelSchema):
    """
    A Schema to serialize SegmentGroups.
    """

    segments = fields.List(fields.Nested(SegmentSchema), load_default=None, required=False)
    segment_groups = fields.List(
        fields.Nested(
            lambda: SegmentGroupSchema(),  # pylint: disable=unnecessary-lambda
        ),
        load_default=None,
        required=False,
    )

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> SegmentGroup:
        """
        Converts the barely typed data dictionary into an actual :class:`.SegmentGroup`
        """
        return SegmentGroup(**data)


# @attr.s(auto_attribs=True, kw_only=True)
# class EdifactStack:
#    """
#    The edifact stack describes where inside an EDIFACT message an information is located.
#    It's closely related to parts of the :class:`.AhbLine` but merges data from multiple lines from the original AHB.
#    """
#    segment_group_key: str = attr.ib(validator=attr.validators.instance_of(str))
#    """ e.g. 'SG2'; data without a segment group are assigned to the the virtual group 'root' """
#    segment_code: str = attr.ib(validator=attr.validators.instance_of(str))
#    """ e.g. 'DTM' """
#    qualifier: str = attr.ib(validator=attr.validators.instance_of(str))
#    """
#    The qualifier can either be the key of an DataElementValuePool entry or the qualifier that is leading/occurs before
#    e.g. 'MS' (this is the main difference to the AHB where qualifier and data element span >1 line)
#    """
#    name: str = attr.ib(validator=attr.validators.instance_of(str))  #: .e.g "MP-ID"
#    format_string: str = attr.ib(validator=attr.validators.instance_of(str))
#    """e.g. '203' to specify how a datetime has to be parsed"""


@attr.s(auto_attribs=True, kw_only=True)
class EdifactStackLevel:
    """
    The EDIFACT stack level describes the hierarchy level of information inside an EDIFACT message.
    """

    #: the name of the level, f.e. 'Dokument' or 'Nachricht' or 'Meldepunkt'
    name: str = attr.ib(validator=attr.validators.instance_of(str))
    #: describes if this level is groupable / if there are multiple instances of this level within the same message
    is_groupable: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True, kw_only=True)
class EdifactStack:
    """
    The EdifactStack describes where inside an EDIFACT message data are found.
    The stack is independent of the actual implementation used to create the EDIFACT (be it XML, JSON whatever).
    """

    #: levels describe the nesting inside an edifact message
    levels: List[EdifactStackLevel] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(EdifactStackLevel),
            iterable_validator=attr.validators.instance_of(list),
        )
    )

    def is_sub_stack_of(self, other: "EdifactStack") -> bool:
        """
        Returns true iff this (self) stack is a sub stack of the other provided stack.
        ([Foo][0][Bar]).is_sub_stack_of([Foo][0]) is true.
        """
        if len(other.levels) > len(self.levels):
            # self cannot be a sub path of other if other is "deeper"
            return False
        for level_self, level_other in zip(other.levels, self.levels):  # , strict=False):  # type:ignore[call-overload]
            # strict is False because it's ok if we stop the iteration if self.levels is "exhausted"; explicit is better
            # the type-ignore for the strict=False is necessary for Python<3.10
            if level_self != level_other:
                return False
        # the iteration stopped meaning that for all levels that both other and self share, they are identical.
        # That's the definition of a sub stack. It also means that any stack is a sub stack of itself.
        return True

    def is_parent_of(self, other: "EdifactStack") -> bool:
        """
        Returns true iff this other stack is a sub stack of self.
        """
        return other.is_sub_stack_of(self)

    def to_json_path(self) -> str:
        """
        Transforms this instance into a JSON Path.
        """
        result: str = "$"
        for level in self.levels:
            result += '["' + level.name + '"]'
            if level.is_groupable:
                result += "[0]"
        return result
