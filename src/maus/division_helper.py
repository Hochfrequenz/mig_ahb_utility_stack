"""
division helper is a module that allow to distinguish electricity ("Strom") and gas ("Gas")
"""

from enum import Enum
from typing import Optional


class Division(str, Enum):
    """
    the possibility to distinguish between electricity and gas
    """

    ELECTRICITY = "ELECTRICITY"  #: strom
    GAS = "GAS"  #: gas


def get_division(field_name: Optional[str]) -> Optional[Division]:
    """
    returns a division if the field name is definitely from that division, None otherwise
    """
    if not field_name:
        return None
    if is_gas_name(field_name) is True:  # type:ignore[union-attr]
        return Division.GAS
    if is_electricity_name(field_name) is True:  # type:ignore[union-attr]
        return Division.ELECTRICITY
    return None


def is_gas_name(field_name: str, _is_recursive: bool = False) -> Optional[bool]:
    """
    returns true iff the field name is definitely a gas field
    """
    if "gas" in field_name.lower():  # maybe use regex `\bgas\b` just to be sure
        return True
    if _is_recursive is False and is_electricity_name(field_name, _is_recursive=True) is True:
        return False
    return None


def is_electricity_name(field_name: str, _is_recursive: bool = False) -> Optional[bool]:
    """
    returns true iff the field name is definitely a strom field
    """
    if "strom" in field_name.lower():  # maybe use regex `\bstrom\b` just to be sure
        return True
    if _is_recursive is False and is_gas_name(field_name, _is_recursive=True) is True:
        return False
    return None
