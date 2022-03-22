"""
A module with internal/private models that are not thought to be used outside the MAUS package itself.
"""

from typing import Callable, List, Optional
from xml.etree.ElementTree import Element

import attrs
from lxml import etree  # type:ignore[import]

from maus.models.edifact_components import EdifactStack, EdifactStackQuery


# pylint:disable=too-few-public-methods
@attrs.define(auto_attribs=True, kw_only=True)
class MigFilterResult:
    """
    the (internal) result of a query path search inside the tree
    """

    is_unique: Optional[bool]  #: True iff unique, None for no results, False for >1 result
    unique_result: Optional[Element]  #: unique element if there is any; None otherwise
    candidates: Optional[List[Element]]  #: list of candidates if there is >1 result


# pylint:disable=too-few-public-methods
@attrs.define(auto_attribs=True, kw_only=True)
class EdifactStackSearchStrategy:
    """
    The search strategy allows to have a compact yet descriptive representation on how the edifact stack search works.
    The alternative to this is a very nested and hard to understand if/else/then structure with lots of branches.
    Any step inside the strategy has three possible outcomes which are represented by the :class:`_XQueryPathResult`:
    1. There is exactly one unique result => return/exit
    2. There are no results => start over again
    3. There are >1 results => apply additional filters
    """

    #: name, e.g. "filter by data element id"
    name: str = attrs.field(validator=attrs.validators.instance_of(str))
    #: the filter is the function that describes the strategy. It consumes the query and (optionally) a list of elements
    filter: Callable[[EdifactStackQuery, Optional[List[Element]]], MigFilterResult] = attrs.field(
        validator=attrs.validators.is_callable()
    )
    #: The unique result strategy is to return an edifact stack for the unique result element
    unique_result_strategy: Callable[[Element], EdifactStack] = attrs.field(validator=attrs.validators.is_callable())
    #: the no result strategy is to apply another filter based on those candidates that lead to no result (fallback)
    no_result_strategy: Optional["EdifactStackSearchStrategy"]
    #: in case of multiple results the next strategy uses the multiple results as input (sharpen)
    multiple_results_strategy: Optional["EdifactStackSearchStrategy"]

    def apply(self, query: EdifactStackQuery, pre_selection: Optional[List[Element]] = None) -> Optional[EdifactStack]:
        """
        Apply the defined strategy until we either have no ideas left or a unique result is found
        """
        # https://stackoverflow.com/questions/47972143/using-attr-with-pylint
        # pylint: disable=not-callable
        filter_result: MigFilterResult = self.filter(query, pre_selection)
        if filter_result.is_unique is True:
            return self.unique_result_strategy(filter_result.unique_result)  # type:ignore[arg-type]
        if filter_result.candidates and len(filter_result.candidates) > 1:
            if self.multiple_results_strategy is not None:
                return self.multiple_results_strategy.apply(query, filter_result.candidates)
            return None
        if self.no_result_strategy is not None:
            return self.no_result_strategy.apply(query, pre_selection)
        return None
