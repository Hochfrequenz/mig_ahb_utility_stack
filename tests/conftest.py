import pytest


@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    """
    This fixture makes sure that the test will use the test case folder as their working directory
    So you can use the directory where the test is living as starting point for your file paths.

    `request` is a built-in pytest fixture
    `fspath`  is the LocalPath to the test module being executed
    `dirname` is the directory of the test module

    Source of this oneliner: https://stackoverflow.com/a/62055409/12907883
    """
    monkeypatch.chdir(request.fspath.dirname)
