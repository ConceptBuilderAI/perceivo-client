"""Request-body cases shared by the convenience-wrapper contract tests.

The table is split across ``tests/_fixtures_body_cases_part*.py`` to keep each
module under the line-count ceiling; this module is the import point and
concatenates the parts in their original order.
"""

from tests._fixtures_body_cases_part1 import BODY_CASES as _PART1
from tests._fixtures_body_cases_part2 import BODY_CASES as _PART2

__all__ = ["BODY_CASES"]

BODY_CASES = [*_PART1, *_PART2]
