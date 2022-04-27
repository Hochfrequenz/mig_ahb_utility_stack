import json
from pathlib import Path
from sys import gettrace

from maus import DeepAnwendungshandbuch
from maus.models.anwendungshandbuch import DeepAnwendungshandbuchSchema


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
