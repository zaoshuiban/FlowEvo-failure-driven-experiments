from typing import List

class Solution:
    def findChampion(self, grid: List[List[int]]) -> int:
        n = len(grid)
        
        for champion in range(n):
            if all(grid[other][champion] == 0 for other in range(n)):
                return champion
        
        return -1