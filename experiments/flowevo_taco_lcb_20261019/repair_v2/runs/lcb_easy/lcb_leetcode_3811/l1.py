class Solution:
    def reverseDegree(self, s: str) -> int:
        total = 0
        for i, ch in enumerate(s, start=1):
            total += i * (ord('z') - ord(ch) + 1)
        return total