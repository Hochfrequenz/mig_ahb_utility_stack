# pylint:disable=too-few-public-methods
"""
EDIFACT components are data structures on different hierarchical levels inside an EDIFACT message.
Components contain not only EDIFACT composits but also segments and segment groups.
"""
import re
from abc import ABC
from enum import Enum
from typing import Callable, List, Optional, Type

import attr
import attrs
from marshmallow import Schema, fields, post_dump, post_load, pre_dump, pre_load  # type:ignore[import]
from marshmallow_enum import EnumField  # type:ignore[import]


class DataElementDataType(str, Enum):
    """
    The Data Element Data Type describes with which kind of data element we're dealing with in a data element.
    This information is set but not used anywhere inside MAUS directly but more of a "service" to downstream code.
    """

    TEXT = "TEXT"  #: plain text, e.g. a name
    DATETIME = "DATETIME"  #: a datetime string, usually as RFC3339
    VALUE_POOL = "VALUE_POOL"  #: the user can choose between different possible values


def derive_data_type_from_segment_code(segment_code: str) -> Optional[DataElementDataType]:
    """
    derives the expected data type from the segment code, e.g. `DATETIME` for DTM segments
    :return: The DataType if it can be derived without any doubt, None otherwise
    """
    if segment_code in {"DTM"}:
        return DataElementDataType.DATETIME
    return None


@attrs.define(auto_attribs=True, kw_only=True)
class DataElement(ABC):
    """
    A data element holds specific kinds of data. It is defined in EDIFACT.
    At least for the German energy market communication any data element has a 4 digit key.
    For example in UTILMD the data element that holds the 13 digit market partner ID is data element '3039'
    """

    discriminator: str = attrs.field(validator=attrs.validators.instance_of(str))
    """ The discriminator uniquely identifies the data element. This _might_ be its key """
    # but could also be a reference or a name
    #: the ID of the data element (e.g. "0062") for the Nachrichten-Referenznummer
    data_element_id: str = attrs.field(validator=attrs.validators.matches_re(r"^\d{4}$"))
    #: the type of data expected to be used with this data element
    entered_input: Optional[str] = attrs.field(validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    """
    If the message which is evaluated contains data for this data element, this is set to a value which is not None.
    The field can either carry a free text or an element from a value pool (depending on the value_type)
    """
    value_type: Optional[DataElementDataType] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(DataElementDataType)), default=None
    )
    """
    The value_type allows to describe which type of data we're expecting to be used within this data element.
    The value_type does not discriminate the type of the data element itself.
    """


class DataElementSchema(Schema):
    """
    A Schema to (de-)serialize DataElements
    """

    discriminator = fields.String(required=True)
    data_element_id = fields.String(required=True)
    entered_input = fields.String(required=False, load_default=None)
    value_type = EnumField(DataElementDataType, required=False)


@attrs.define(auto_attribs=True, kw_only=True)
class DataElementFreeText(DataElement):
    """
    A DataElementFreeText is a data element that allows entering arbitrary data.
    This is the main difference to the :class:`DataElementValuePool` which has a finite set of allowed values attached.
    """

    value_type: Optional[DataElementDataType] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(DataElementDataType)),  # type:ignore[arg-type]
        default=DataElementDataType.TEXT,
    )
    ahb_expression: str = attrs.field(validator=attrs.validators.instance_of(str))
    """any freetext data element has an ahb expression attached. Could be 'X' but also 'M [13]'"""


class DataElementFreeTextSchema(DataElementSchema):
    """
    A Schema to serialize DataElementFreeTexts
    """

    ahb_expression = fields.String(required=True)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> DataElementFreeText:
        """
        Converts the barely typed data dictionary into an actual :class:`.DataElementFreeText`
        """
        return DataElementFreeText(**data)


# pylint: disable=unused-argument
def _check_that_string_is_not_whitespace_or_empty(instance, attribute, value):
    """
    Check that string in the instance attribute value is not empty
    """
    if not value:
        raise ValueError(f"The string {attribute.name} must not be None or empty")
    if len(value.strip()) == 0:
        raise ValueError(f"The string {attribute.name} must not consist only of whitespace: '{value}'")


#: a pattern that matches most of the qualifiers we find in the AHBs
_simple_edifact_qualifier_pattern = re.compile(r"^([A-Z\d]+)|(\d+\.\d+[a-z])$")

#: a pattern that matches the GABi qualifiers: They contain with "-" and lower case "i"/"o"/"n"
gabi_edifact_qualifier_pattern = re.compile(r"^(GABi)?[A-Z\d\-]+(RLM(o|m)T)?$")


def _check_is_edifact_qualifier(instance, attribute, value):
    """
    Checks that the given attribute is a valid EDIFACT qualifier.
    Raises a ValueError if not.
    """
    _check_that_string_is_not_whitespace_or_empty(instance, attribute, value)
    simple_match = _simple_edifact_qualifier_pattern.match(value)
    if simple_match is not None:
        return
    gabi_match = gabi_edifact_qualifier_pattern.match(value)
    if gabi_match is not None:
        return
    raise ValueError(f"The qualifier {attribute.name} '{value}' is invalid")


@attrs.define(auto_attribs=True, kw_only=True)
class ValuePoolEntry:
    """
    A value pool entry contains the EDIFACT qualifier, a meaning (German text) and an ahb expression.
    A value pool consists of 1 to n ValuePoolEntries.
    The data element 3055 in UTILMD is a good example for a value pool.
    It is used in the segments NAD+MS and NAD+MR. Its ValuePoolEntries are:
    - (key: "9", meaning: "GS1", ahb_expression: "X")
    - (key: "293", meaning: "DE, BDEW", ahb_expression: "X")
    - (key: "332", meaning: "DE, DVGW", ahb_expression: "X")
    """

    #: the qualifier in edifact, might be e.g. "E01", "D", "9", "1.1a", "G_0057"
    qualifier: str = attr.field(validator=_check_is_edifact_qualifier)
    #: the meaning as it is written in the AHB (e.g. "Einzug", "Entwurfs-Version", "GS1", "Codeliste Gas G_0057"
    meaning: str = attr.field(validator=attrs.validators.instance_of(str))
    #: the ahb expression, in most cases this is a simple "X"; it must not be empty
    ahb_expression: str = attr.field(validator=_check_that_string_is_not_whitespace_or_empty)
    # must not be empty (if so, the value pool entry should not be included of the result)


class ValuePoolEntrySchema(Schema):
    """
    A Schema to serialize ValuePoolEntries
    """

    # this looks like a plain Dict[str,str] but we prefer typed access over loose string key value pairs
    qualifier = fields.String(required=True)
    meaning = fields.String(required=True)
    ahb_expression = fields.String(required=True)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> ValuePoolEntry:
        """
        Converts the barely typed data dictionary into an actual :class:`.ValuePoolEntry`
        """
        return ValuePoolEntry(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class DataElementValuePool(DataElement):
    """
    A DataElementValuePool is a data element with a finite set of allowed values.
    These allowed values are referred to as keys of the "value pool".
    The value pool is defined both on MIG level and AHB level
    The set of values allowed according to the AHB is always a subset of the values allowed according to the MIG.
    """

    value_type: Optional[DataElementDataType] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(DataElementDataType)),  # type:ignore[arg-type]
        default=DataElementDataType.VALUE_POOL,
    )  #: type of the value, if known
    value_pool: List[ValuePoolEntry] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(ValuePoolEntry),
            iterable_validator=attrs.validators.instance_of(list),
        )
    )
    """
    The value pool contains at least one value :class:`.ValuePoolEntry`
    """


class DataElementValuePoolSchema(DataElementSchema):
    """
    A Schema to serialize DataElementValuePool
    """

    value_pool = fields.List(fields.Nested(ValuePoolEntrySchema), required=True)

    # pylint:disable=unused-argument
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

    free_text: Optional[DataElementFreeText] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(DataElementFreeText))
    )
    value_pool: Optional[DataElementValuePool] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(DataElementValuePool))
    )


class _FreeTextOrValuePoolSchema(Schema):
    """
    A schema that represents data of the kind Union[DataElementFreeText,DataElementValuePool]
    There is a python package for that: https://github.com/adamboche/python-marshmallow-union
    but is only has 15 stars; not sure if it's worth the dependency
    """

    # disable unnecessary lambda warning because of circular imports
    free_text = fields.Nested("DataElementFreeTextSchema", allow_none=True, required=False)
    value_pool = fields.Nested("DataElementValuePoolSchema", required=False, allow_none=True)
    # see https://github.com/fuhrysteve/marshmallow-jsonschema/issues/164

    # pylint:disable= unused-argument
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

    # pylint:disable= unused-argument
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

    # pylint:disable= unused-argument
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

    # pylint:disable= unused-argument
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


@attrs.define(auto_attribs=True, kw_only=True)
class SegmentLevel(ABC):
    """
    SegmentLevel describes @annika: what does it describe?
    """

    discriminator: str  # no validator here, because it might be None on initialization and will be set later (trust me)
    ahb_expression: str = attrs.field(validator=attrs.validators.instance_of(str))


class SegmentLevelSchema(Schema):
    """
    A Schema to serialize SegmentLevels
    """

    discriminator = fields.String(required=True)
    ahb_expression = fields.String(required=True)


@attrs.define(auto_attribs=True, kw_only=True)
class Segment(SegmentLevel):
    """
    A Segment contains multiple data elements.
    """

    data_elements: List[DataElement]
    section_name: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(str)), default=None
    )
    """
    For the MIG matching it might be necessary to know the section in which the data element occured in the AHB.
    This might be necessary to e.g. distinguish gas and electricity fields which look the same otherwise.
    See e.g. UTILMD 'Geplante Turnusablesung des MSB (Strom)' vs. 'Geplante Turnusablesung des NB (Gas)'
    """


class SegmentSchema(SegmentLevelSchema):
    """
    A Schema to serialize Segments
    """

    data_elements = fields.List(fields.Nested(_FreeTextOrValuePoolSchema))
    section_name = fields.String(required=False)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> Segment:
        """
        Converts the barely typed data dictionary into an actual :class:`.Segment`
        """
        return Segment(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class SegmentGroup(SegmentLevel):
    """
    A segment group that contains segments and nested groups.
    On root level of a message there might be a "virtual" segment group of all segments that formally don't have a group
    This group has the key "root".
    """

    segments: Optional[List[Segment]] = attrs.field(
        validator=attrs.validators.optional(
            attrs.validators.deep_iterable(
                member_validator=attrs.validators.instance_of(Segment),
                iterable_validator=attrs.validators.instance_of(list),
            )
        ),
        default=None,
    )  #: the segments inside this very group
    segment_groups: Optional[List["SegmentGroup"]] = attrs.field(
        default=None
    )  #: groups that are nested into this group

    def find_segments(self, predicate: Callable[[Segment], bool], search_recursively: bool = True) -> List[Segment]:
        """
        Search for a segment that matches the predicate (in this group and subgroups if 'search_recursively' is set),
        Return results, if found. Return empty list otherwise.
        """
        result: List[Segment] = []
        if self.segments is not None:
            for segment in self.segments:
                if predicate(segment):
                    result.append(segment)
        if search_recursively and self.segment_groups is not None:
            for sub_group in self.segment_groups:
                sub_result = sub_group.find_segments(predicate, search_recursively)
                result += sub_result
        return result


class SegmentGroupSchema(SegmentLevelSchema):
    """
    A Schema to serialize SegmentGroups.
    """

    segments = fields.List(fields.Nested(SegmentSchema), load_default=None, required=False)
    segment_groups = fields.List(
        fields.Nested("SegmentGroupSchema"),
        # see https://github.com/fuhrysteve/marshmallow-jsonschema/issues/164
        load_default=None,
        required=False,
    )

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> SegmentGroup:
        """
        Converts the barely typed data dictionary into an actual :class:`.SegmentGroup`
        """
        return SegmentGroup(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class EdifactStackLevel:
    """
    The EDIFACT stack level describes the hierarchy level of information inside an EDIFACT message.
    """

    #: the name of the level, e.g. 'Dokument' or 'Nachricht' or 'Meldepunkt'
    name: str = attrs.field(validator=attrs.validators.instance_of(str))
    #: describes if this level is groupable / if there are multiple instances of this level within the same message
    is_groupable: bool = attrs.field(validator=attrs.validators.instance_of(bool))
    #: the index if present (e.g. 0)
    index: Optional[int] = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(int))
    )


#: a pattern that matches parts of the json path: https://regex101.com/r/iQzdXK/1
_level_pattern = re.compile(r"\[\"(?P<level_name>[^\[\]]+?)\"\](?:\[(?P<index>\d+)\])?")


@attrs.define(auto_attribs=True, kw_only=True)
class EdifactStack:
    """
    The EdifactStack describes where inside an EDIFACT message data are found.
    The stack is independent of the actual implementation used to create the EDIFACT (be it XML, JSON whatever).
    """

    #: levels describe the nesting inside an edifact message
    levels: List[EdifactStackLevel] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(EdifactStackLevel),
            iterable_validator=attrs.validators.instance_of(list),
        )
    )

    @staticmethod
    def from_json_path(json_path: str) -> "EdifactStack":
        """
        reads a json path as it is created by "to_json_path" and returns the corresponding edifact stack
        """
        levels: List[EdifactStackLevel] = []
        for level_match in _level_pattern.finditer(json_path):
            level = EdifactStackLevel(name=level_match["level_name"], is_groupable=level_match["index"] is not None)
            if level.is_groupable:
                level.index = int(level_match["index"])
            levels.append(level)
        return EdifactStack(levels=levels)

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
        # https://stackoverflow.com/questions/47972143/using-attr-with-pylint
        # pylint: disable=not-an-iterable
        for level in self.levels:
            result += '["' + level.name + '"]'
            if level.index is not None:
                result += f"[{level.index}]"
            elif level.is_groupable:
                result += "[0]"
        return result


@attrs.define(auto_attribs=True, kw_only=True)
class EdifactStackQuery:
    """
    The EdifactStackQuery contains the data you need to provide to a MIG reader to return you the :class:`EdifactStack`
    of an element
    """

    #: the key of the segment group, e.g. 'root' or 'SG5' or 'SG12'
    segment_group_key: str = attrs.field(validator=attrs.validators.instance_of(str))
    #: the segment code, e.g. 'NAD' or 'DTM'
    segment_code: str = attrs.field(validator=attrs.validators.matches_re("^[A-Z]+$"))
    #: the data element id, e.g. '0068'
    data_element_id: str = attrs.field(validator=attrs.validators.matches_re(r"^\d{4}$"))
    #: the name of the element, e.g. "MP-ID" or "Kundennummer" or "Identifikator"; Is None for Value Pools
    name: Optional[str] = attrs.field(validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    predecessor_qualifier: Optional[str] = attrs.field(
        default=None, validator=attrs.validators.optional(_check_is_edifact_qualifier)
    )  # GABi-RLMEV wtf
    """
    Some names are not really unique. e.g. all date time fields carry more or less the same name in the AHB.
    So to distinguish between them you may provide the predecissing qualifier.
    In case of 'DTM+137++what_youre_looking_for' the predecessor qualifier is '137'
    """
    section_name: Optional[str] = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str))
    )
    """
    The section name (e.g. 'Nachrichten-Kopfsegment') might also be used for MIG<->AHB matching
    if the name is too broad or not unique.
    """
