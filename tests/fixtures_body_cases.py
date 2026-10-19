"""Request-body cases shared by the convenience-wrapper contract tests.

The table is assembled from ``tests/_fixtures_body_cases_part*.py``.
"""

from tests._fixtures_body_cases_part1 import BODY_CASES as _PART1
from tests._fixtures_body_cases_part2 import BODY_CASES as _PART2

__all__ = ["BODY_CASES"]

BODY_CASES = [*_PART1, *_PART2]
