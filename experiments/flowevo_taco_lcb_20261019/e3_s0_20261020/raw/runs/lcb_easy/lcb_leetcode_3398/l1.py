from typing import List

class Solution:
    def canMakeSquare(self, grid: List[List[str]]) -> bool:
        for i in range(2):
            for j in range(2):
                black = 0
                white = 0
                
                for r in range(i, i + 2):
                    for c in range(j, j + 2):
                        if grid[r][c] == "B":
                            black += 1
                        else:
                            white += 1
                
                if black >= 3 or white >= 3:
                    return True
                    
        return False