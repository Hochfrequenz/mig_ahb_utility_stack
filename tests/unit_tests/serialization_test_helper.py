import json
from typing import Type, TypeVar, Union

import cattrs as cattrs
from marshmallow import Schema  # type:ignore[import]

T = TypeVar("T")


def assert_serialization_roundtrip(
    serializable_object: T, schema_or_type: Union[Schema, Type], expected_json_dict: dict
) -> T:
    """
    Serializes the serializable_object using the provided schema or cattrs if no schema was provided,
    asserts, that the result is equal to the expected_json_dict
    then deserializes it again and asserts on equality with the original serializable_object

    :returns the deserialized_object
    """
    json_string: str
    actual_json_dict: dict
    if isinstance(schema_or_type, Schema):
        schema: Schema = schema_or_type
        json_string = schema.dumps(serializable_object)
        actual_json_dict = json.loads(json_string)
    elif isinstance(schema_or_type, Type):
        actual_json_dict = cattrs.unstructure(serializable_object)
        json_string = json.dumps(actual_json_dict)
    else:
        raise ValueError(f"Unspported type {schema_or_type}")
    assert json_string is not None
    assert actual_json_dict == expected_json_dict
    deserialized_object: T
    if isinstance(schema_or_type, Schema):
        deserialized_object = schema.loads(json_data=json_string)
    elif isinstance(schema_or_type, Type):
        deserialized_object = cattrs.structure_attrs_fromdict(actual_json_dict, type(serializable_object))
    assert isinstance(deserialized_object, type(serializable_object))
    assert deserialized_object == serializable_object
    return deserialized_object
