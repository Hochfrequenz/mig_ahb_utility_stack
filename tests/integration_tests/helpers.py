import json
from pathlib import Path
from sys import gettrace
from typing import Optional

import attrs

from maus.mig_ahb_matching import to_deep_ahb
from maus.models.anwendungshandbuch import (
    DeepAnwendungshandbuch,
    DeepAnwendungshandbuchSchema,
    FlatAnwendungshandbuch,
    FlatAnwendungshandbuchSchema,
)
from maus.models.message_implementation_guide import SegmentGroupHierarchy, SegmentGroupHierarchySchema
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from maus.reader.mig_xml_reader import MigXmlReader


def is_in_debug_mode() -> bool:
    """
    returns true if it is called in debug mode.
    Generally it's wrong to behave differently depending on "from where" the code is called.
    In our test cases we want to know if the tests run in debug mode in order to decide if testdata should be actively
    updated.
    :return: true iff debug mode
    """
    return gettrace() is not None


def should_write_to_submodule() -> bool:
    """
    returns true if tests should write to the submodule (e.g. updated MAUS s' or AHBs)
    """
    # return True # enable this line to overwrite the test data
    return is_in_debug_mode()


def write_to_file_or_assert_equality(deep_ahb: DeepAnwendungshandbuch, file_path: Path) -> None:
    """
    writes the given maus/deep ahb into the provided file path or read it from there and assert equality.
    The decision (write vs. read) is met by 'should_write_to_submodule'
    :return:
    """
    write_into_submodule: bool = should_write_to_submodule()
    schema = DeepAnwendungshandbuchSchema()
    if write_into_submodule:
        with open(file_path, "w+", encoding="utf-8") as outfile:
            json_dict = schema.dump(deep_ahb)
            json.dump(json_dict, outfile, ensure_ascii=True, indent=2, sort_keys=True)
    else:
        with open(file_path, "r", encoding="utf-8") as infile:
            json_content = json.load(infile)
            expected_maus = schema.load(json_content)
        assert deep_ahb == expected_maus


@attrs.define(kw_only=True)
class IntegrationTestResult:
    """
    A class that contains test results
    """

    flat_ahb: FlatAnwendungshandbuch = attrs.field(validator=attrs.validators.instance_of(FlatAnwendungshandbuch))
    segment_group_hierarchy: SegmentGroupHierarchy = attrs.field(
        validator=attrs.validators.instance_of(SegmentGroupHierarchy)
    )
    deep_ahb: DeepAnwendungshandbuch = attrs.field(validator=attrs.validators.instance_of(DeepAnwendungshandbuch))
    maus: DeepAnwendungshandbuch = attrs.field(validator=attrs.validators.instance_of(DeepAnwendungshandbuch))


def create_maus_and_assert(
    sgh_path: Path, template_path: Path, maus_path: Path, flat_ahb_path: Path
) -> IntegrationTestResult:
    """
    The repetitive part of every integration test so far:
    read the CSV into a FlatAhb, read the SGH from the file, read the template, join both AHB and MIG into a MAUS
    """
    with open(flat_ahb_path, "r", encoding="utf-8") as flat_ahb_file:
        flat_ahb = FlatAnwendungshandbuchSchema().load(json.load(flat_ahb_file))
    with open(sgh_path, "r", encoding="utf-8") as sgh_file:
        sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
    mig_reader = MigXmlReader(template_path)
    actual_deep_ahb = to_deep_ahb(flat_ahb, sgh, mig_reader)
    actual_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
    maus = DeepAnwendungshandbuchSchema().loads(actual_json)  # maus is a copy of the (unchanged) actual_deep_ahb
    actual_maus_json = DeepAnwendungshandbuchSchema().dumps(maus, ensure_ascii=True, sort_keys=True, indent=True)
    assert actual_maus_json is not None
    write_to_file_or_assert_equality(maus, maus_path)
    result = IntegrationTestResult(flat_ahb=flat_ahb, segment_group_hierarchy=sgh, deep_ahb=actual_deep_ahb, maus=maus)
    assert (
        len(
            list(
                x
                for x in list(result.deep_ahb.get_all_value_pools())
                if len(list(y for y in x.value_pool if y.ahb_expression is None)) > 0
            )
        )
        == 0
    )
    assert len(list(seg for seg in list(result.deep_ahb.find_segments()) if seg.ahb_expression is None)) == 0
    assert (
        len(list(sg for sg in list(result.deep_ahb.find_segment_groups(lambda _: True)) if sg.ahb_expression is None))
        == 0
    )
    return result
