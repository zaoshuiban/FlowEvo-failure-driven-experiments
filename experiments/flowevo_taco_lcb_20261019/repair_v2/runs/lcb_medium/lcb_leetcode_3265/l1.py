from typing import List

class Solution:
    def maximumSubarraySum(self, nums: List[int], k: int) -> int:
        # Maps a value to the minimum prefix sum before an occurrence of it.
        min_prefix = {}
        prefix = 0
        ans = None

        for x in nums:
            # Check whether a previous occurrence can be the start of a good subarray.
            for target in (x - k, x + k):
                if target in min_prefix:
                    current_sum = prefix + x - min_prefix[target]
                    if ans is None or current_sum > ans:
                        ans = current_sum

            # Store prefix sum before this element for future subarrays.
            if x not in min_prefix or prefix < min_prefix[x]:
                min_prefix[x] = prefix

            prefix += x

        return ans if ans is not None else 0