from typing import List

class Solution:
    def numberOfPoints(self, nums: List[List[int]]) -> int:
        covered = set()
        for start, end in nums:
            covered.update(range(start, end + 1))
        return len(covered)