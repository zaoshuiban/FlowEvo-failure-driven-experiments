from typing import List
from collections import defaultdict


class Solution:
    def maxSubarraySum(self, nums: List[int]) -> int:
        n = len(nums)

        size = 1
        while size < n:
            size <<= 1

        NEG = -10**18
        m = size << 1

        total = [0] * m
        pref = [0] * m
        suff = [0] * m

        pref_act = [NEG] * m
        suff_act = [NEG] * m
        best_act = [NEG] * m

        # Initialize leaves
        for i, val in enumerate(nums):
            idx = size + i
            total[idx] = val
            if val > 0:
                pref[idx] = val
                suff[idx] = val
            else:
                pref[idx] = 0
                suff[idx] = 0

            pref_act[idx] = val
            suff_act[idx] = val
            best_act[idx] = val

        def pull(i: int) -> None:
            left = i << 1
            right = left | 1

            sl = total[left]
            sr = total[right]

            total[i] = sl + sr

            a = pref[left]
            b = sl + pref[right]
            pref[i] = a if a > b else b

            a = suff[right]
            b = sr + suff[left]
            suff[i] = a if a > b else b

            pla = pref_act[left]
            pra = pref_act[right]

            has_left_active = pla != NEG

            a = pla
            if has_left_active:
                b = sl + pref[right]
            else:
                b = sl + pra
            pref_act[i] = a if a > b else b

            sla = suff_act[left]
            sra = suff_act[right]

            has_right_active = pra != NEG

            a = sra
            if has_right_active:
                b = sr + suff[left]
            else:
                b = sr + sla
            suff_act[i] = a if a > b else b

            best = best_act[left]
            if best_act[right] > best:
                best = best_act[right]

            crossing1 = sla + pref[right]
            crossing2 = suff[left] + pra

            if crossing1 > best:
                best = crossing1
            if crossing2 > best:
                best = crossing2

            best_act[i] = best

        for i in range(size - 1, 0, -1):
            pull(i)

        def set_inactive(pos: int) -> None:
            i = size + pos
            total[i] = 0
            pref[i] = 0
            suff[i] = 0
            pref_act[i] = NEG
            suff_act[i] = NEG
            best_act[i] = NEG

            i >>= 1
            while i:
                pull(i)
                i >>= 1

        def set_active(pos: int, val: int) -> None:
            i = size + pos
            total[i] = val

            if val > 0:
                pref[i] = val
                suff[i] = val
            else:
                pref[i] = 0
                suff[i] = 0

            pref_act[i] = val
            suff_act[i] = val
            best_act[i] = val

            i >>= 1
            while i:
                pull(i)
                i >>= 1

        positions = defaultdict(list)
        for i, val in enumerate(nums):
            if val < 0:
                positions[val].append(i)

        answer = best_act[1]

        for arr in positions.values():
            if len(arr) == n:
                continue

            for idx in arr:
                set_inactive(idx)

            if best_act[1] > answer:
                answer = best_act[1]

            for idx in arr:
                set_active(idx, nums[idx])

        return answer