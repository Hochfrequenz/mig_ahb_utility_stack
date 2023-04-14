from pathlib import Path

import pytest  # type:ignore[import]

from maus.reader.tree_to_sgh import check_file_can_be_parsed_as_tree, check_youngest_tree_is_parseable, read_tree


class TestTreeToSgh:
    """
    Tests the parser for .tree files
    """

    @pytest.mark.datafiles("./migs/FV2210/segment_group_hierarchies/UTILTS1.1a.tree")
    @pytest.mark.parametrize("filename", ["UTILTS1.1a.tree"])
    def test_read_tree(self, datafiles, filename: str):
        tree = read_tree(Path(datafiles / Path(filename)))
        assert tree is not None

    @pytest.mark.datafiles("./migs/FV2210/segment_group_hierarchies/UTILTS1.1a.tree")
    @pytest.mark.parametrize("filename", ["UTILTS1.1a.tree"])
    def test_check_file_can_be_parsed_as_tree(self, datafiles, filename: str):
        check_file_can_be_parsed_as_tree(Path(datafiles / Path(filename)))

    @pytest.mark.datafiles("./migs/FV2210/segment_group_hierarchies/UTILTS1.1a.tree")
    def test_check_youngest_tree_is_parseable(self, datafiles):
        check_youngest_tree_is_parseable(Path(datafiles))

    def test_get_edifact_format_error(self):
        something_which_is_not_a_str = 17
        with pytest.raises(ValueError):
            _ = read_tree(something_which_is_not_a_str)  # type:ignore[arg-type]
