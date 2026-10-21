class Solution:
    def maxSubstringLength(self, s: str, k: int) -> bool:
        if k == 0:
            return True

        n = len(s)
        nums = [ord(ch) - ord('a') for ch in s]

        first = [n] * 26
        last = [-1] * 26

        for i, x in enumerate(nums):
            if first[x] == n:
                first[x] = i
            last[x] = i

        intervals = []

        # Every valid special substring must start at the first occurrence
        # of the character at its left endpoint.
        for c in range(26):
            l = first[c]
            if l == n:
                continue

            r = last[c]
            i = l
            valid = True

            while i <= r:
                x = nums[i]

                if first[x] < l:
                    valid = False
                    break

                if last[x] > r:
                    r = last[x]

                i += 1

            if not valid:
                continue

            # The whole string is not allowed.
            if l == 0 and r == n - 1:
                continue

            intervals.append((r, l))

        # Maximum number of non-overlapping intervals: greedy by ending position.
        intervals.sort()
        count = 0
        last_end = -1

        for r, l in intervals:
            if l > last_end:
                count += 1
                last_end = r

                if count >= k:
                    return True

        return False