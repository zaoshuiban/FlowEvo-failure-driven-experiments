from typing import List

class Solution:
    def minDifference(self, nums: List[int]) -> int:
        n = len(nums)

        # Minimum possible maximum difference for intervals to be stabbed
        # by two points whose distance is at most D.
        def distance_two_ok(intervals, D):
            if not intervals:
                return True

            min_r = 10**30
            max_l = -10**30

            for l, r in intervals:
                if r < min_r:
                    min_r = r
                if l > max_l:
                    max_l = l

            # One point can hit all intervals.
            if max_l <= min_r:
                return True

            # We need p <= q, q - p <= D, and q can be chosen as max_l.
            need_left = -10**30
            for l, r in intervals:
                if r < max_l and l > need_left:
                    need_left = l

            lower = max(1, max_l - D, need_left)
            upper = min(min_r, max_l - 1)
            return lower <= upper

        # Whether all intervals can be stabbed by at most two points.
        def two_stab_ok(intervals):
            if not intervals:
                return True

            # Greedily choose the smallest right endpoint.
            p = 10**30
            for l, r in intervals:
                if r < p:
                    p = r

            max_l = -10**30
            min_r = 10**30
            exists = False

            for l, r in intervals:
                if l > p:
                    exists = True
                    if l > max_l:
                        max_l = l
                    if r < min_r:
                        min_r = r

            if not exists:
                return True

            return max_l <= min_r

        def feasible(D):
            # Fixed adjacent pairs must already satisfy D.
            for i in range(n - 1):
                if nums[i] != -1 and nums[i + 1] != -1:
                    if abs(nums[i] - nums[i + 1]) > D:
                        return False

            intervals_a = []
            intervals_b = []
            core_bad = False

            i = 0
            while i < n:
                if nums[i] != -1:
                    i += 1
                    continue

                j = i
                while j < n and nums[j] == -1:
                    j += 1

                length = j - i
                left = nums[i - 1] if i > 0 else -1
                right = nums[j] if j < n else -1

                if left == -1 and right == -1:
                    pass

                elif left == -1:
                    l = max(1, right - D)
                    r = right + D
                    intervals_a.append((l, r))
                    intervals_b.append((l, r))

                elif right == -1:
                    l = max(1, left - D)
                    r = left + D
                    intervals_a.append((l, r))
                    intervals_b.append((l, r))

                else:
                    if length == 1:
                        l = max(left, right) - D
                        r = min(left, right) + D

                        if l > r:
                            return False

                        l = max(1, l)
                        intervals_a.append((l, r))
                        intervals_b.append((l, r))

                    else:
                        l1 = max(1, left - D)
                        r1 = left + D
                        intervals_a.append((l1, r1))

                        l2 = max(1, right - D)
                        r2 = right + D
                        intervals_a.append((l2, r2))

                        l = max(left, right) - D
                        r = min(left, right) + D

                        if l <= r:
                            l = max(1, l)
                            intervals_b.append((l, r))
                        else:
                            core_bad = True

                i = j

            # Case 1: the two chosen values are within distance D.
            if distance_two_ok(intervals_a, D):
                return True

            # Case 2: each missing segment can be filled using one common value.
            if not core_bad and two_stab_ok(intervals_b):
                return True

            return False

        max_fixed = 0
        for i in range(n - 1):
            if nums[i] != -1 and nums[i + 1] != -1:
                max_fixed = max(max_fixed, abs(nums[i] - nums[i + 1]))

        lo = max_fixed - 1
        hi = 10**9

        while hi - lo > 1:
            mid = (lo + hi) // 2
            if feasible(mid):
                hi = mid
            else:
                lo = mid

        return hi