from typing import List

class Solution:
    def beautifulSplits(self, nums: List[int]) -> int:
        n = len(nums)
        if n < 3:
            return 0

        # Z-function to check where nums1 is a prefix of nums2.
        z = [0] * n
        l = r = 0
        for i in range(1, n):
            if i < r:
                z[i] = min(r - i, z[i - l])
            while i + z[i] < n and nums[z[i]] == nums[i + z[i]]:
                z[i] += 1
            if i + z[i] > r:
                l, r = i, i + z[i]

        good_first = [False] * n
        count_a = 0

        # i is the length of nums1, and also the start of nums2.
        for i in range(1, n):
            if z[i] >= i:
                good_first[i] = True
                if 2 * i <= n - 1:
                    count_a += n - 2 * i

        # Count cases where nums2 is a prefix of nums3 using LCP DP.
        nxt = [0] * (n + 1)
        count_b = 0
        both = 0

        for i in range(n - 1, 0, -1):
            cur = [0] * (n + 1)
            ai = nums[i]
            limit = (n + i) // 2

            for j in range(n - 1, i, -1):
                if ai == nums[j]:
                    v = nxt[j + 1] + 1
                    cur[j] = v

                    if j <= limit and v >= j - i:
                        count_b += 1
                        if good_first[i] and j >= 2 * i:
                            both += 1

            nxt = cur

        return count_a + count_b - both