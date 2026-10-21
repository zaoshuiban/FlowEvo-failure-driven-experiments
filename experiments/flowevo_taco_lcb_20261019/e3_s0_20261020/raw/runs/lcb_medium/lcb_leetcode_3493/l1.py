class Solution:
    def maxOperations(self, s: str) -> int:
        ans = 0
        ones = 0
        prev = ''

        for ch in s:
            if ch == '1':
                ones += 1
            elif prev == '1':
                ans += ones
            prev = ch

        return ans