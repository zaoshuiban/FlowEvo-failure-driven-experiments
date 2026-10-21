from typing import List

class Solution:
    def areaOfMaxDiagonal(self, dimensions: List[List[int]]) -> int:
        max_diagonal = -1
        max_area = 0

        for length, width in dimensions:
            diagonal_squared = length * length + width * width
            area = length * width

            if diagonal_squared > max_diagonal:
                max_diagonal = diagonal_squared
                max_area = area
            elif diagonal_squared == max_diagonal:
                max_area = max(max_area, area)

        return max_area