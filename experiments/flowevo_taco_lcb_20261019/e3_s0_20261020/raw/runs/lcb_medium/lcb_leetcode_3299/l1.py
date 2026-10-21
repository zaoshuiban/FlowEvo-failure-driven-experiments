from typing import List
from collections import Counter

class Solution:
    def maximumLength(self, nums: List[int]) -> int:
        freq = Counter(nums)
        ans = 1
        
        if 1 in freq:
            c = freq[1]
            if c % 2 == 0:
                c -= 1
            ans = max(ans, c)
        
        for x in freq:
            if x == 1:
                continue
            
            cur = x
            level = 0
            
            while cur in freq:
                ans = max(ans, 2 * level + 1)
                
                if freq[cur] < 2:
                    break
                
                cur *= cur
                level += 1
        
        return ans