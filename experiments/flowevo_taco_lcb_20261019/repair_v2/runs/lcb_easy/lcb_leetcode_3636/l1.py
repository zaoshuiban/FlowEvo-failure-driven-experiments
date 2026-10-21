class Solution:
    def isBalanced(self, num: str) -> bool:
        even_sum = sum(int(num[i]) for i in range(0, len(num), 2))
        odd_sum = sum(int(num[i]) for i in range(1, len(num), 2))
        return even_sum == odd_sum