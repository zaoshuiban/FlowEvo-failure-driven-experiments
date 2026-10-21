from typing import List

class Solution:
    def longestValidSubstring(self, word: str, forbidden: List[str]) -> int:
        forbidden_set = set(forbidden)
        left = 0
        answer = 0

        for right in range(len(word)):
            max_len = min(10, right - left + 1)

            for length in range(1, max_len + 1):
                if word[right - length + 1:right + 1] in forbidden_set:
                    left = right - length + 2
                    break

            answer = max(answer, right - left + 1)

        return answer