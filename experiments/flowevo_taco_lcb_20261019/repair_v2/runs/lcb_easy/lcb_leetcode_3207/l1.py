class Solution:
    def findMinimumOperations(self, s1: str, s2: str, s3: str) -> int:
        limit = min(len(s1), len(s2), len(s3))
        common = 0

        while common < limit and s1[common] == s2[common] == s3[common]:
            common += 1

        if common == 0:
            return -1

        return (len(s1) - common) + (len(s2) - common) + (len(s3) - common)