from typing import List

class Solution:
    def numberOfRightTriangles(self, grid: List[List[int]]) -> int:
        rows = len(grid)
        cols = len(grid[0])

        row_count = [sum(row) for row in grid]
        col_count = [0] * cols

        for i in range(rows):
            for j in range(cols):
                col_count[j] += grid[i][j]

        answer = 0

        for i in range(rows):
            for j in range(cols):
                if grid[i][j] == 1:
                    answer += (row_count[i] - 1) * (col_count[j] - 1)

        return answer