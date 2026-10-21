from typing import List

class Solution:
    def maximumSumSubsequence(self, nums: List[int], queries: List[List[int]]) -> int:
        MOD = 10**9 + 7
        NEG = -10**18

        n = len(nums)
        size = 1
        while size < n:
            size <<= 1

        tree = [(0, NEG, NEG, NEG) for _ in range(2 * size)]

        for i, value in enumerate(nums):
            tree[size + i] = (0, NEG, NEG, value)

        def merge(left, right):
            l00, l01, l10, l11 = left
            r00, r01, r10, r11 = right

            return (
                max(l00 + max(r00, r10), l01 + r00),
                max(l00 + max(r01, r11), l01 + r01),
                max(l10 + max(r00, r10), l11 + r00),
                max(l10 + max(r01, r11), l11 + r01),
            )

        for i in range(size - 1, 0, -1):
            tree[i] = merge(tree[i << 1], tree[(i << 1) | 1])

        answer = 0

        for pos, value in queries:
            idx = size + pos
            tree[idx] = (0, NEG, NEG, value)
            idx >>= 1

            while idx:
                tree[idx] = merge(tree[idx << 1], tree[(idx << 1) | 1])
                idx >>= 1

            best = max(tree[1])
            answer = (answer + best) % MOD

        return answer