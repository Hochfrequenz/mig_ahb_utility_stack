"""
A module that reads AHBs from a given CSV file
"""
import csv
import logging
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Sequence, TextIO, Tuple

from maus.models.anwendungshandbuch import AhbLine, AhbMetaInformation, FlatAnwendungshandbuch
from maus.models.edifact_components import gabi_edifact_qualifier_pattern

_pruefi_pattern = re.compile(r"^\d{5}$")  #: five digits
_value_pool_entry_pattern = re.compile(r"^[A-Z0-9\-i]{2,}$")  # i for GABi -- why?
_numeric_value_pool_entry_pattern = re.compile(r"^\d+(?:\.\d+)?[a-z]?$")
_ebd_code_pattern = re.compile(r"^(E|G)_\d+$")
_segment_group_pattern = re.compile(r"^SG\d+$")


# pylint:disable=too-few-public-methods
class FlatAhbReader(ABC):
    """
    An AHB Reader reads AHB data from a source and is able to convert them to a :class:`.FlatAnwendungshandbuch`
    """

    @abstractmethod
    def to_flat_ahb(self) -> FlatAnwendungshandbuch:
        """
        convert the read data into a flat anwendungshandbuch
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")


class FlatAhbCsvReader(FlatAhbReader):
    """
    reads csv files and returns AHBs
    """

    def __init__(self, file_path: Path, pruefidentifikator: Optional[str] = None, encoding="utf-8", delimiter=","):
        self.rows: List[AhbLine] = []
        self._logger = logging.getLogger()
        self.current_section_name: Optional[str] = None
        self.pruefidentifikator = pruefidentifikator
        self.delimiter = delimiter
        with open(file_path, "r", encoding=encoding) as infile:
            # current_section_name: Optional[str]
            for row in self.get_raw_rows(infile):
                ahb_line = self.raw_ahb_row_to_ahbline(row)
                if ahb_line is None:
                    continue
                self.rows.append(ahb_line)

    def get_raw_rows(self, file_handle: TextIO) -> List[dict]:
        """
        reads the input file and returns an iterator over raw lines.
        Override this method if your data source is not a CSV file
        """
        reader = csv.DictReader(file_handle, delimiter=self.delimiter)
        if not self.pruefidentifikator:
            self.pruefidentifikator = FlatAhbCsvReader._get_name_of_expression_column(reader.fieldnames)
        if not self.pruefidentifikator:
            raise ValueError("Cannot find column name for ahb expression")
        return list(reader)

    def raw_ahb_row_to_ahbline(self, ahb_row: dict) -> Optional[AhbLine]:
        """
        Converts a row of the raw/scraped AHB into the AhbLine data structure.
        Returns None for rows that are skipped.
        Override this method is your column names/input data structure differs.
        """
        value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
            ahb_row["Codes und Qualifier"], ahb_row["Beschreibung"]
        )
        segment_group: Optional[str] = None
        if FlatAhbCsvReader._is_segment_group(ahb_row["Segment Gruppe"]):
            segment_group = ahb_row["Segment Gruppe"]
        elif len(ahb_row["Segment Gruppe"]) >= 3:
            self.current_section_name = ahb_row["Segment Gruppe"].strip() or None  # e.g. "Nachrichten-Kopfsegment"
            self._logger.debug("Processing %s section '%s'", self.pruefidentifikator, self.current_section_name)
            return None  # possibly a section heading like "Nachrichten-Endesegment"
            # this is different from segment group = None which is value for e.g. the UNH
        result: AhbLine = AhbLine(
            guid=uuid.uuid4(),
            segment_group_key=segment_group,
            segment_code=ahb_row["Segment"] or None,
            data_element=ahb_row["Datenelement"] or None,
            value_pool_entry=value_pool_entry,
            ahb_expression=ahb_row[self.pruefidentifikator] or None,
            name=description,
            section_name=self.current_section_name,
        )
        return result

    @staticmethod
    def separate_value_pool_entry_and_name(
        x: Optional[str], y: Optional[str]  # pylint:disable=invalid-name
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        The PDFs are so broken, that sometimes the Codes column contains the description of the line instead of the code
        This function returns a value_pool_entry at index 0, a possible description at index 1, even if they're mixed up
        in the source files.
        """
        if x is not None:
            x = x.strip()
        if y is not None:
            y = y.strip()
        if FlatAhbCsvReader._is_value_pool_entry(x) and not FlatAhbCsvReader._is_value_pool_entry(y):
            return x, y or None
        if FlatAhbCsvReader._is_value_pool_entry(x) and FlatAhbCsvReader._is_value_pool_entry(y):
            # Both look like a value pool entry. This typically happens e.g. for date qualifiers or code lists
            return x, y
        return y or None, x or None

    @staticmethod
    def _is_value_pool_entry(candidate: Optional[str]) -> bool:
        """
        Returns true iff the provided candidate is a possible value pool entry.
        """
        if not candidate:
            return False
        if _value_pool_entry_pattern.match(candidate) is not None:
            return True
        # numbers alone might be value pool entries even if they don't match the regex
        # we don't use "isdigit" because isdigit e.g. does not match '1.2'
        if _numeric_value_pool_entry_pattern.match(candidate) is not None:
            return True
        if len(candidate) == 1 and candidate.upper() == candidate:
            return True
        if gabi_edifact_qualifier_pattern.match(candidate) is not None:
            return True
        return _ebd_code_pattern.match(candidate) is not None

    @staticmethod
    def _is_segment_group(candidate: Optional[str]) -> bool:
        """
        Returns true iff the provided candidate is a possible segment group
        """
        if not candidate:
            return False
        return _value_pool_entry_pattern.match(candidate) is not None

    @staticmethod
    def _get_name_of_expression_column(field_names: Optional[Sequence[str]]) -> Optional[str]:
        """
        Gets the name of the column that holds the AHB expressions.
        This allows us to read any AHB without a priori knowledge of its pruefidentifikator.

        :param field_names: list of fieldnames
        :return: the first field name that is a 5 digit name or None if none is found.
        """
        if not field_names:
            return None
        for field_name in field_names:
            if _pruefi_pattern.match(field_name):
                return field_name
        return None

    def to_flat_ahb(self) -> FlatAnwendungshandbuch:
        """
        Converts the content of the CSV file to a FlatAnwendungshandbuch.
        :return:
        """
        return FlatAnwendungshandbuch(
            meta=AhbMetaInformation(
                pruefidentifikator=self.pruefidentifikator  # type:ignore[arg-type]
            ),
            lines=[row for row in self.rows if row.holds_any_information()],
        )
