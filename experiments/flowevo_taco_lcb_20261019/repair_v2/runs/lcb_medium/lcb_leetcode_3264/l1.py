from typing import List

class Solution:
    def maximumPoints(self, enemyEnergies: List[int], currentEnergy: int) -> int:
        mn = min(enemyEnergies)
        if currentEnergy < mn:
            return 0
        return (currentEnergy + sum(enemyEnergies) - mn) // mn