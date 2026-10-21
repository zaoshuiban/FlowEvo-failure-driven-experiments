from typing import List

class Solution:
    def maxIncreasingGroups(self, usageLimits: List[int]) -> int:
        usageLimits.sort()
        total = 0
        groups = 0
        
        for limit in usageLimits:
            total += limit
            needed = (groups + 1) * (groups + 2) // 2
            if total >= needed:
                groups += 1
                
        return groups