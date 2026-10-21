from typing import List

class Solution:
    def minProcessingTime(self, processorTime: List[int], tasks: List[int]) -> int:
        processorTime.sort()
        tasks.sort(reverse=True)
        
        answer = 0
        for i, start_time in enumerate(processorTime):
            answer = max(answer, start_time + tasks[4 * i])
        
        return answer