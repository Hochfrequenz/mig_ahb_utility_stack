from pathlib import Path

import pytest  # type:ignore[import]

from maus.reader.tree_to_sgh import read_tree


class TestTreeToSgh:
    """
    Tests the parser for .tree files
    """

    @pytest.mark.datafiles("./migs/FV2210/segment_group_hierarchies/UTILTS1.1a.tree")
    @pytest.mark.parametrize("filename", ["UTILTS1.1a.tree"])
    def test_get_edifact_format(self, datafiles, filename: str):
        tree = read_tree(Path(datafiles / Path(filename)))
        assert tree is not None
