from pathlib import Path
from typing import List, Optional

import pytest  # type:ignore[import]

from maus.reader.flat_ahb_reader import FlatAhbCsvReader


class TestAhbCsvReader:
    """
    Tests the ahb_csv_reader
    """

    @pytest.mark.parametrize(
        "field_names, expected_column_name",
        [
            pytest.param(
                [
                    "Segment Gruppe",
                    "Segment",
                    "Datenelement",
                    "Codes und Qualifier",
                    "Beschreibung",
                    "11042",
                    "Bedingung",
                ],
                "11042",
            ),
            pytest.param(["foo", "bar"], None),
            pytest.param(None, None),
            pytest.param([], None),
        ],
    )
    def test_ahb_expression_column_finder(self, field_names: List[str], expected_column_name: Optional[str]):
        actual = FlatAhbCsvReader._get_name_of_expression_column(field_names)
        assert actual == expected_column_name

    @pytest.mark.parametrize(
        "value, expected_is_value_pool_entry",
        [
            pytest.param(None, False),
            pytest.param("", False),
            pytest.param("E01", True),
        ],
    )
    def test_is_value_pool_entry(self, value: Optional[str], expected_is_value_pool_entry: bool):
        actual = FlatAhbCsvReader._is_value_pool_entry(value)
        assert actual == expected_is_value_pool_entry

    @pytest.mark.parametrize(
        "value, expected_is_segment_group",
        [
            pytest.param(None, False),
            pytest.param("", False),
            pytest.param("Nachrichten-Endesegment", False),
            pytest.param("SG4", True),
            pytest.param("SG12", True),
        ],
    )
    def test_is_segment_group(self, value: Optional[str], expected_is_segment_group: bool):
        actual = FlatAhbCsvReader._is_segment_group(value)
        assert actual == expected_is_segment_group

    @pytest.mark.parametrize(
        "csv_code, csv_beschreibung, expected_code, expected_beschreibung",
        [
            pytest.param("Nachrichten-Referenznummer", None, None, "Nachrichten-Referenznummer"),
            pytest.param("137", "Dokumenten-/Nachrichtendatum/-zeit", "137", "Dokumenten-/Nachrichtendatum/-zeit"),
            pytest.param(
                "Datum oder Uhrzeit oderZeitspanne, Wert", None, None, "Datum oder Uhrzeit oderZeitspanne, Wert"
            ),
            pytest.param("303", "CCYYMMDDHHMMZZZ", "303", "CCYYMMDDHHMMZZZ"),
            pytest.param("9", "GS1", "9", "GS1"),
            pytest.param("IC", "Informationskontakt", "IC", "Informationskontakt"),
            pytest.param(
                "MS",
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
                "MS",
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
            ),
            pytest.param("TN", "Transaktions-Referenznummer", "TN", "Transaktions-Referenznummer"),
            pytest.param(
                "293",
                "DE, BDEW (Bundesverband der Energie- und Wasserwirtschaft e.V.)",
                "293",
                "DE, BDEW (Bundesverband der Energie- und Wasserwirtschaft e.V.)",
            ),
            pytest.param(
                "1.2",
                "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                "1.2",
                "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                id="format version reqote",
            ),
            pytest.param(
                "D",
                "Entwurfs-Version",
                "D",
                "Entwurfs-Version",
                id="entwurfs version reqote",
            ),
            pytest.param(
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
                "MS ",  # <-- has a trailing white space
                "MS",  # <-- has no trailing whitespace
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
                id="strip inputs; utilmd absender",
            ),
            pytest.param("EBD Nr. E_0456", "E_0456", "E_0456", "EBD Nr. E_0456", id="EBD Name in IFSTA"),
            pytest.param(
                "2.0d",
                "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                "2.0d",
                "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                id="iftsta version",
            ),
        ],
    )
    def test_code_description_separation(
        self,
        csv_code: Optional[str],
        csv_beschreibung: Optional[str],
        expected_code: Optional[str],
        expected_beschreibung: Optional[str],
    ):
        actual_code, actual_beschreibung = FlatAhbCsvReader.separate_value_pool_entry_and_name(
            csv_code, csv_beschreibung
        )
        assert actual_code == expected_code
        assert actual_beschreibung == expected_beschreibung

    @pytest.mark.datafiles("./ahbs/FV2204/UTILMD/11042.csv")
    def test_csv_file_reading_11042(self, datafiles):
        path_to_csv: Path = datafiles / "11042.csv"
        reader = FlatAhbCsvReader(file_path=path_to_csv)
        assert len(reader.rows) == 846
        # first row assertions
        first_row = reader.rows[0]
        assert first_row.segment_code == "UNH"
        assert first_row.ahb_expression == "Muss"

        # last row assertions
        last_row = reader.rows[845]
        assert last_row.segment_code == "UNT"
        assert last_row.data_element == "0062"
        assert last_row.name == "Nachrichten-Referenznummer"
        assert last_row.ahb_expression == "X"

        flat_ahb = reader.to_flat_ahb()
        assert len(flat_ahb.lines) < len(reader.rows)  # filter out the empty lines
        assert flat_ahb.get_segment_groups() == [None, "SG2", "SG3", "SG4", "SG5", "SG6", "SG8", "SG9", "SG10", "SG12"]
