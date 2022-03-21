"""
This module contains helper methods that compare strings, especially names from AHB and MIG.
"""
from typing import Optional


def make_name_comparable(orig_str: str) -> str:
    """
    Removes all the characters that could be a problem when matching names from the AHB with names from the MIG
    """
    result: str = orig_str.lower()
    for removable_character in [" ", "-", "\n"]:
        result = result.replace(removable_character, "")
    return result


def are_similar_names(name_x: Optional[str], name_y: Optional[str]) -> bool:
    """
    Returns true if name_x and name_y are somehow similar.
    "Somehow similar" in this context means, that all the artefacts from text to word to PDF + scraping
    + human errors might add up to something which explains the difference between name_x and name_y.
    """
    if (name_x and not name_y) or (name_y and not name_x):
        return False
    if (not name_x) and (not name_y):
        return True
    # neither name_x nor name_y are None below this line
    return make_name_comparable(name_x) == make_name_comparable(name_y)  # type:ignore[arg-type]
