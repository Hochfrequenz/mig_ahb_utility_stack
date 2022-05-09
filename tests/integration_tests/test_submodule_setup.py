from pathlib import Path

import pytest  # type:ignore[import]


class TestSubmoduleSetup:
    """
    Tests that the private submodule can be accessed from the integration tests.
    (This is not expected to work for anyone who does not have access to Hochfrequenz/edifact-templates).
    """

    @pytest.mark.datafiles("./edifact-templates/edi/APERAK/APERAK2.1f.template")
    def test_aperak_file_can_be_accessed(self, datafiles):
        path_to_file: Path = Path(datafiles) / Path("APERAK2.1f.template")
        with open(path_to_file, "r") as infile:
            lines = infile.readlines()
            assert len(lines) > 50  # there has to be something, no matter what
