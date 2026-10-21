from typing import List

class Solution:
    def relocateMarbles(self, nums: List[int], moveFrom: List[int], moveTo: List[int]) -> List[int]:
        occupied = set(nums)

        for start, end in zip(moveFrom, moveTo):
            occupied.remove(start)
            occupied.add(end)

        return sorted(occupied)