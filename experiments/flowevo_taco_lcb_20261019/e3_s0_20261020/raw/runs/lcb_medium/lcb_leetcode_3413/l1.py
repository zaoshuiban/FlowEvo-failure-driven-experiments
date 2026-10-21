from typing import List

class Solution:
    def findWinningPlayer(self, skills: List[int], k: int) -> int:
        champion = 0
        streak = 0

        for i in range(1, len(skills)):
            if skills[champion] > skills[i]:
                streak += 1
            else:
                champion = i
                streak = 1

            if streak == k:
                return champion

        return champion