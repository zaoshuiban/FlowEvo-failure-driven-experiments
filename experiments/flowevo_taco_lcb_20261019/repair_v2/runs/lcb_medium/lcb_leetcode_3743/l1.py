from typing import List

class Solution:
    def maxFreeTime(self, eventTime: int, k: int, startTime: List[int], endTime: List[int]) -> int:
        n = len(startTime)
        gaps = [0] * (n + 1)

        gaps[0] = startTime[0]
        for i in range(1, n):
            gaps[i] = startTime[i] - endTime[i - 1]
        gaps[n] = eventTime - endTime[-1]

        window_size = k + 1
        current = sum(gaps[:window_size])
        answer = current

        for i in range(window_size, n + 1):
            current += gaps[i] - gaps[i - window_size]
            answer = max(answer, current)

        return answer