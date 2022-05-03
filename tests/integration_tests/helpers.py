import json
from pathlib import Path
from sys import gettrace

import attrs

from maus import DeepAnwendungshandbuch, SegmentGroupHierarchy, to_deep_ahb
from maus.deep_ahb_mig_joiner import replace_discriminators_with_edifact_stack
from maus.models.anwendungshandbuch import DeepAnwendungshandbuchSchema, FlatAnwendungshandbuch
from maus.models.message_implementation_guide import SegmentGroupHierarchySchema
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from maus.reader.mig_reader import MigXmlReader


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
    csv_path: Path, sgh_path: Path, template_path: Path, maus_path: Path
) -> IntegrationTestResult:
    """
    The repetitive part of every integration test so far:
    read the CSV into a FlatAhb, read the SGH from the file, read the template, join both AHB and MIG into a MAUS
    """
    reader = FlatAhbCsvReader(file_path=csv_path)
    flat_ahb = reader.to_flat_ahb()
    with open(sgh_path, "r", encoding="utf-8") as sgh_file:
        sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
    actual_deep_ahb = to_deep_ahb(flat_ahb, sgh)
    actual_json = DeepAnwendungshandbuchSchema().dumps(actual_deep_ahb, ensure_ascii=True, sort_keys=True)
    mig_reader = MigXmlReader(template_path)
    maus = DeepAnwendungshandbuchSchema().loads(actual_json)  # maus is a copy of the (unchanged) actual_deep_ahb
    assert mig_reader is not None
    replace_discriminators_with_edifact_stack(maus, mig_reader, ignore_errors=False)
    actual_maus_json = DeepAnwendungshandbuchSchema().dumps(maus, ensure_ascii=True, sort_keys=True, indent=True)
    assert actual_maus_json is not None
    write_to_file_or_assert_equality(maus, maus_path)
    result = IntegrationTestResult(flat_ahb=flat_ahb, segment_group_hierarchy=sgh, deep_ahb=actual_deep_ahb, maus=maus)
    return result
