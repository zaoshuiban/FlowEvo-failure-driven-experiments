from typing import List

class Solution:
    def findMissingAndRepeatedValues(self, grid: List[List[int]]) -> List[int]:
        n = len(grid)
        total_numbers = n * n
        seen = set()
        repeated = 0
        actual_sum = 0

        for row in grid:
            for value in row:
                actual_sum += value
                if value in seen:
                    repeated = value
                else:
                    seen.add(value)

        expected_sum = total_numbers * (total_numbers + 1) // 2
        missing = expected_sum + repeated - actual_sum

        return [repeated, missing]