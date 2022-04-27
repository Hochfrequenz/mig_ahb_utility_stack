from sys import gettrace


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
    return is_in_debug_mode()
