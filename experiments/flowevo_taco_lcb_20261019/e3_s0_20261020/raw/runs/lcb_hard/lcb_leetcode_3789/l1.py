from typing import List

class Solution:
    def maxSubarrays(self, n: int, conflictingPairs: List[List[int]]) -> int:
        by_end = [[] for _ in range(n + 1)]
        
        for idx, (x, y) in enumerate(conflictingPairs):
            a, b = min(x, y), max(x, y)
            by_end[b].append((a, idx))
        
        count = [0] * (n + 1)
        owner = [-1] * (n + 1)
        gain = [0] * len(conflictingPairs)
        
        max1 = 0
        max2 = 0
        base = 0
        
        for r in range(1, n + 1):
            for a, idx in by_end[r]:
                if count[a] == 0:
                    if a > max1:
                        max2 = max1
                        max1 = a
                    elif a > max2:
                        max2 = a
                    owner[a] = idx
                
                count[a] += 1
            
            base += r - max1
            
            if max1 > 0 and count[max1] == 1:
                gain[owner[max1]] += max1 - max2
        
        return base + (max(gain) if gain else 0)