from typing import List

class Solution:
    def unmarkedSumArray(self, nums: List[int], queries: List[List[int]]) -> List[int]:
        n = len(nums)
        total = sum(nums)
        marked = [False] * n
        ordered = sorted((value, index) for index, value in enumerate(nums))
        
        pointer = 0
        answer = []
        
        for index, k in queries:
            if not marked[index]:
                marked[index] = True
                total -= nums[index]
            
            while k > 0:
                while pointer < n and marked[ordered[pointer][1]]:
                    pointer += 1
                
                if pointer == n:
                    break
                
                value, pos = ordered[pointer]
                marked[pos] = True
                total -= value
                pointer += 1
                k -= 1
            
            answer.append(total)
        
        return answer