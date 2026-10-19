"""Endpoint cases for the complete convenience-wrapper matrix.

The table is assembled from ``tests/_fixtures_wrapper_cases_part*.py``.
"""

from tests._fixtures_wrapper_cases_part1 import CASES as _PART1
from tests._fixtures_wrapper_cases_part1 import B
from tests._fixtures_wrapper_cases_part2 import CASES as _PART2
from tests._fixtures_wrapper_cases_part3 import CASES as _PART3
from tests._fixtures_wrapper_cases_part4 import CASES as _PART4
from tests._fixtures_wrapper_cases_part5 import CASES as _PART5

__all__ = ["CASES", "B"]

CASES = [*_PART1, *_PART2, *_PART3, *_PART4, *_PART5]
