"""
This module manages EDIFACT related stuff. It's basically a helper module to avoid stringly typed parameters.
"""

import re
from typing import Optional

import attrs
from efoli import get_format_of_pruefidentifikator, EdifactFormat, EdifactFormatVersion

_PRUEFI_REGEX = r"^[1-9]\d{4}$"
pruefidentifikator_pattern = re.compile(_PRUEFI_REGEX)


def is_edifact_boilerplate(segment_code: Optional[str]) -> bool:
    """
    returns true iff this segment is not relevant in a sense that it has to be validated or merged with the AHB
    """
    if not segment_code:
        return True
    return segment_code.strip() in {"UNT", "UNZ"}

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
