from pathlib import Path
from typing import Optional

import pytest  # type:ignore[import]

from maus.reader.mig_reader import MigXmlReader

ALL_MIG_XML_FILES = pytest.mark.datafiles(
    "./unittests/migs/FV2204/template_xmls/mscons_1154.xml",
)


class TestMigXmlReader:
    """
    Tests the behaviour of the Message Implementation Guide model
    """

    @pytest.mark.parametrize(
        "xml_string, expected_format",
        [
            pytest.param('<?xml version="1.0"?><MSCONS></MSCONS>', "MSCONS"),
            pytest.param('<?xml version="1.0"?><UTILMD></UTILMD>', "UTILMD"),
        ],
    )
    def test_get_edifact_format(self, xml_string: str, expected_format: str):
        reader = MigXmlReader(xml_string)
        assert reader.get_format_name() == expected_format

    @pytest.mark.parametrize(
        "x,y, expected_result",
        [
            pytest.param(None, "", True),
            pytest.param("", "", True),
            pytest.param("X", "X", True),
            pytest.param("X", "x", True),
            pytest.param("X", "y", False),
        ],
    )
    def test_are_similar_names(self, x: Optional[str], y: Optional[str], expected_result: bool):
        actual = MigXmlReader.are_similar_names(x, y)
        assert actual == expected_result

    @ALL_MIG_XML_FILES
    @pytest.mark.parametrize(
        "segment_group_key, segment_key, data_element_id, name, expected_path",
        [
            pytest.param(
                "SG1",
                "RFF",
                "1154",
                "Prüfidentifikator",
                '$["Dokument"][0]["Nachricht"][0]["Prüfidentifikator"][0]["ID"]',
            ),
        ],
    )
    def test_simple_paths(
        self,
        datafiles,
        segment_group_key: str,
        segment_key: str,
        data_element_id: str,
        name: Optional[str],
        expected_path: str,
    ):
        reader = MigXmlReader(Path(datafiles) / "mscons_1154.xml")
        assert reader.get_format_name() == "MSCONS"
        assert reader.get_edifact_seed_path(segment_group_key, segment_key, data_element_id, name) == expected_path
