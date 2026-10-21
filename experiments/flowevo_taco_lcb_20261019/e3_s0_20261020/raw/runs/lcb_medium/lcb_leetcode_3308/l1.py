class Solution:
    def lastNonEmptyString(self, s: str) -> str:
        freq = [0] * 26
        for ch in s:
            freq[ord(ch) - ord('a')] += 1

        max_freq = max(freq)
        seen = [0] * 26
        ans = []

        for ch in s:
            idx = ord(ch) - ord('a')
            seen[idx] += 1
            if freq[idx] == max_freq and seen[idx] == freq[idx]:
                ans.append(ch)

        return ''.join(ans)