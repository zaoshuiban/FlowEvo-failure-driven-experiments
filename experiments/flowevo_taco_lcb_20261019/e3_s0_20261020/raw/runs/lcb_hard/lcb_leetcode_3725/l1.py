from typing import List

class Solution:
    def minMaxSubarraySum(self, nums: List[int], k: int) -> int:
        n = len(nums)
        t = k + 1

        def c2(x: int) -> int:
            if x < 2:
                return 0
            return x * (x - 1) // 2

        def count_pairs(a: int, b: int) -> int:
            return c2(t) - c2(t - a) - c2(t - b) + c2(t - a - b)

        total = 0

        # Contribution as minimum
        prev_less = [-1] * n
        stack = []
        for i, x in enumerate(nums):
            while stack and nums[stack[-1]] >= x:
                stack.pop()
            prev_less[i] = stack[-1] if stack else -1
            stack.append(i)

        next_le = [n] * n
        stack.clear()
        for i in range(n - 1, -1, -1):
            x = nums[i]
            while stack and nums[stack[-1]] > x:
                stack.pop()
            next_le[i] = stack[-1] if stack else n
            stack.append(i)

        for i, x in enumerate(nums):
            left = i - prev_less[i]
            right = next_le[i] - i
            total += x * count_pairs(left, right)

        # Contribution as maximum
        prev_greater = [-1] * n
        stack.clear()
        for i, x in enumerate(nums):
            while stack and nums[stack[-1]] <= x:
                stack.pop()
            prev_greater[i] = stack[-1] if stack else -1
            stack.append(i)

        next_ge = [n] * n
        stack.clear()
        for i in range(n - 1, -1, -1):
            x = nums[i]
            while stack and nums[stack[-1]] < x:
                stack.pop()
            next_ge[i] = stack[-1] if stack else n
            stack.append(i)

        for i, x in enumerate(nums):
            left = i - prev_greater[i]
            right = next_ge[i] - i
            total += x * count_pairs(left, right)

        return total