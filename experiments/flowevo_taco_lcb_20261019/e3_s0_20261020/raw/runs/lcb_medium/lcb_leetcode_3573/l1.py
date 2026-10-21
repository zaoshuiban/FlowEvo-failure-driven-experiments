class Solution:
    def validSubstringCount(self, word1: str, word2: str) -> int:
        n = len(word1)
        req = [0] * 26
        for ch in word2:
            req[ord(ch) - ord('a')] += 1

        have = [0] * 26
        missing = sum(1 for x in req if x > 0)

        ans = 0
        right = 0

        for left in range(n):
            while right < n and missing > 0:
                c = ord(word1[right]) - ord('a')
                have[c] += 1
                if req[c] > 0 and have[c] == req[c]:
                    missing -= 1
                right += 1

            if missing == 0:
                ans += n - right + 1

            if left < right:
                c = ord(word1[left]) - ord('a')
                if req[c] > 0 and have[c] == req[c]:
                    missing += 1
                have[c] -= 1

        return ans