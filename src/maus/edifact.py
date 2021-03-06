"""
This module manages EDIFACT related stuff. It's basically a helper module to avoid stringly typed parameters.
"""
import datetime
import re
from enum import Enum
from typing import Dict, Optional

pruefidentifikator_pattern = re.compile(r"^[1-9]\d{4}$")


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
    "37": EdifactFormat.PARTIN,
    "11": EdifactFormat.UTILMD,
    "25": EdifactFormat.UTILTS,
    "91": EdifactFormat.CONTRL,
    "92": EdifactFormat.APERAK,
}


class EdifactFormatVersion(str, Enum):
    """
    One format version refers to the period in which an AHB is valid.
    """

    FV2104 = "FV2104"  #: valid from 2021-04-01 until 2021-10-01
    FV2110 = "FV2110"  #: valid from 2021-10-01 until 2022-04-01
    FV2210 = "FV2210"  #: valid from 2022-10-01 onwards ("MaKo 2022", was 2204 previously)
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
    return EdifactFormatVersion.FV2210


def is_edifact_boilerplate(segment_code: Optional[str]) -> bool:
    """
    returns true iff this segment is not relevant in a sense that it has to be validated or merged with the AHB
    """
    if not segment_code:
        return True
    return segment_code.strip() in {"UNT", "UNZ"}


def pruefidentifikator_to_format(pruefidentifikator: str) -> Optional[EdifactFormat]:
    """
    returns the format corresponding to a given pruefi
    """
    if not pruefidentifikator:
        raise ValueError("The pruefidentifikator must not be falsy")
    if not pruefidentifikator_pattern.match(pruefidentifikator):
        raise ValueError(f"The pruefidentifikator '{pruefidentifikator}' is invalid.")
    try:
        return _edifact_mapping[pruefidentifikator[:2]]
    except KeyError:
        return None
