"""
This module manages EDIFACT related stuff. It's basically a helper module to avoid stringly typed parameters.
"""
import datetime
import re
from enum import Enum
from typing import Dict, Optional

import attrs

_PRUEFI_REGEX = r"^[1-9]\d{4}$"
pruefidentifikator_pattern = re.compile(_PRUEFI_REGEX)


# pylint: disable=too-few-public-methods
class EdifactFormat(str, Enum):
    """
    existing EDIFACT formats
    """

    APERAK = "APERAK"
    COMDIS = "COMDIS"  #: communication dispute
    CONTRL = "CONTRL"  #: control messages
    IFTSTA = "IFTSTA"  #: Multimodaler Statusbericht
    INSRPT = "INSRPT"  #: Prüfbericht
    INVOIC = "INVOIC"  #: invoice
    MSCONS = "MSCONS"  #: meter readings
    ORDCHG = "ORDCHG"  #: changing an order
    ORDERS = "ORDERS"  #: orders
    ORDRSP = "ORDRSP"  #: orders response
    PRICAT = "PRICAT"  #: price catalogue
    QUOTES = "QUOTES"  #: quotes
    REMADV = "REMADV"  #: zahlungsavis
    REQOTE = "REQOTE"  #: request quote
    PARTIN = "PARTIN"  #: market partner data
    UTILMD = "UTILMD"  #: utilities master data
    UTILTS = "UTILTS"  #: formula

    def __str__(self):
        return self.value


_edifact_mapping: Dict[str, EdifactFormat] = {
    "99": EdifactFormat.APERAK,
    "29": EdifactFormat.COMDIS,
    "21": EdifactFormat.IFTSTA,
    "23": EdifactFormat.INSRPT,
    "31": EdifactFormat.INVOIC,
    "13": EdifactFormat.MSCONS,
    "39": EdifactFormat.ORDCHG,
    "17": EdifactFormat.ORDERS,
    "19": EdifactFormat.ORDRSP,
    "27": EdifactFormat.PRICAT,
    "15": EdifactFormat.QUOTES,
    "33": EdifactFormat.REMADV,
    "35": EdifactFormat.REQOTE,
    "37": EdifactFormat.PARTIN,
    "11": EdifactFormat.UTILMD,
    "25": EdifactFormat.UTILTS,
    "91": EdifactFormat.CONTRL,
    "92": EdifactFormat.APERAK,
    "44": EdifactFormat.UTILMD,  # UTILMD for GAS since FV2310
    "55": EdifactFormat.UTILMD,  # UTILMD for STROM since FV2310
}


class EdifactFormatVersion(str, Enum):
    """
    One format version refers to the period in which an AHB is valid.
    """

    FV2104 = "FV2104"  #: valid from 2021-04-01 until 2021-10-01
    FV2110 = "FV2110"  #: valid from 2021-10-01 until 2022-04-01
    FV2210 = "FV2210"  #: valid from 2022-10-01 onwards ("MaKo 2022", was 2204 previously)
    FV2304 = "FV2304"  #: valid from 2023-04-01 onwards
    FV2310 = "FV2310"  #: valid from 2023-10-01 onwards
    FV2404 = "FV2404"  #: valid from 2024-04-01 onwards
    # whenever you add another value here, please also make sure to add its key date to get_edifact_format_version below

    def __str__(self):
        return self.value


def get_edifact_format_version(key_date: datetime.datetime) -> EdifactFormatVersion:
    """
    :return: the edifact format version that is valid on the specified key date
    """
    if key_date < datetime.datetime(2021, 9, 30, 22, 0, 0, 0, tzinfo=datetime.timezone.utc):
        return EdifactFormatVersion.FV2104
    if key_date < datetime.datetime(2022, 9, 30, 22, 0, 0, 0, tzinfo=datetime.timezone.utc):
        return EdifactFormatVersion.FV2110
    if key_date < datetime.datetime(2023, 3, 31, 22, 0, 0, 0, tzinfo=datetime.timezone.utc):
        return EdifactFormatVersion.FV2210
    if key_date < datetime.datetime(2023, 9, 30, 22, 0, 0, 0, tzinfo=datetime.timezone.utc):
        return EdifactFormatVersion.FV2304
    if key_date < datetime.datetime(2024, 3, 31, 22, 0, 0, 0, tzinfo=datetime.timezone.utc):
        return EdifactFormatVersion.FV2310
    return EdifactFormatVersion.FV2404


def get_current_edifact_format_version() -> EdifactFormatVersion:
    """
    returns the edifact_format_version that is valid as of now
    """
    tz_aware_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    return get_edifact_format_version(tz_aware_now)


def is_edifact_boilerplate(segment_code: Optional[str]) -> bool:
    """
    returns true iff this segment is not relevant in a sense that it has to be validated or merged with the AHB
    """
    if not segment_code:
        return True
    return segment_code.strip() in {"UNT", "UNZ"}


def get_format_of_pruefidentifikator(pruefidentifikator: str) -> EdifactFormat:
    """
    returns the format corresponding to a given pruefi
    """
    if not pruefidentifikator:
        raise ValueError("The pruefidentifikator must not be falsy")
    if not pruefidentifikator_pattern.match(pruefidentifikator):
        raise ValueError(f"The pruefidentifikator '{pruefidentifikator}' is invalid.")
    try:
        return _edifact_mapping[pruefidentifikator[:2]]
    except KeyError as key_error:
        raise ValueError(f"No Edifact format was found for pruefidentifikator '{pruefidentifikator}'.") from key_error


# pylint:disable=unused-argument
def _check_that_pruefi_and_format_are_consistent(instance: "EdiMetaData", attribute, value: str):
    """
    The value is the pruefidentifikator, the instance is the EdiMetaData instance.
    This validator raises an ValueError if the pruefidentifikator is not consistent with the instance.edifact_format.
    """
    actual_format = instance.edifact_format
    expected_format = get_format_of_pruefidentifikator(value)
    if actual_format != expected_format:
        raise ValueError(f"'{value}' is incompatible with '{actual_format}'; expected '{expected_format}' instead")


@attrs.define(kw_only=True, frozen=True, auto_attribs=True)
class EdiMetaData:
    """
    a container that contains edifact-related metadata
    """

    pruefidentifikator: str = attrs.field(
        validator=attrs.validators.and_(
            attrs.validators.instance_of(str),
            attrs.validators.matches_re(_PRUEFI_REGEX),
            _check_that_pruefi_and_format_are_consistent,
        )
    )
    """
    The pruefidentifikator, e.g. '11042'
    """
    edifact_format: EdifactFormat = attrs.field(validator=attrs.validators.instance_of(EdifactFormat))
    """
    The Edifact Format, e.g. 'UTILMD'
    """

    @edifact_format.default
    def _get_format_from_pruefidentifikator(self):
        return get_format_of_pruefidentifikator(self.pruefidentifikator)

    edifact_format_version: EdifactFormatVersion = attrs.field(
        validator=attrs.validators.instance_of(EdifactFormatVersion)
    )
    """
    The Edifact Format Version, e.g. 'FV2210'
    """
