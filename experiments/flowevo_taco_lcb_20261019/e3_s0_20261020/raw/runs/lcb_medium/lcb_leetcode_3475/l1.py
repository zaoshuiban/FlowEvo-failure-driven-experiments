from typing import List

class Solution:
    def minOperations(self, nums: List[int]) -> int:
        a = nums[:]
        n = len(a)
        operations = 0

        for i in range(n - 2):
            if a[i] == 0:
                operations += 1
                a[i] ^= 1
                a[i + 1] ^= 1
                a[i + 2] ^= 1

        return operations if all(x == 1 for x in a) else -1