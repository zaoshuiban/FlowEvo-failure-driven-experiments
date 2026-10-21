class Solution:
    def findLatestTime(self, s: str) -> str:
        for hour in range(11, -1, -1):
            for minute in range(59, -1, -1):
                time = f"{hour:02d}:{minute:02d}"
                if all(a == '?' or a == b for a, b in zip(s, time)):
                    return time
        return ""