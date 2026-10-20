"""Endpoint cases for the complete convenience-wrapper matrix.

The table is split across ``tests/_fixtures_wrapper_cases_part*.py`` to keep
each module under the line-count ceiling; this module is the import point and
concatenates the parts in their original order.
"""

from tests._fixtures_wrapper_cases_part1 import CASES as _PART1
from tests._fixtures_wrapper_cases_part1 import B
from tests._fixtures_wrapper_cases_part2 import CASES as _PART2
from tests._fixtures_wrapper_cases_part3 import CASES as _PART3
from tests._fixtures_wrapper_cases_part4 import CASES as _PART4
from tests._fixtures_wrapper_cases_part5 import CASES as _PART5

__all__ = ["CASES", "B"]

CASES = [*_PART1, *_PART2, *_PART3, *_PART4, *_PART5]
