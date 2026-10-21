class Solution:
    def minLength(self, s: str, numOps: int) -> int:
        n = len(s)

        groups = []
        i = 0
        while i < n:
            j = i
            while j < n and s[j] == s[i]:
                j += 1
            groups.append(j - i)
            i = j

        # Minimum flips needed to make s alternating, i.e. max run length <= 1.
        mismatches = 0
        for i, ch in enumerate(s):
            if int(ch) != (i & 1):
                mismatches += 1
        alt_cost = min(mismatches, n - mismatches)

        def can(limit: int) -> bool:
            if limit == 1:
                return alt_cost <= numOps

            ops = 0
            for length in groups:
                ops += length // (limit + 1)
                if ops > numOps:
                    return False
            return ops <= numOps

        lo, hi = 1, n
        while lo < hi:
            mid = (lo + hi) // 2
            if can(mid):
                hi = mid
            else:
                lo = mid + 1

        return lo