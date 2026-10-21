from typing import List
from functools import cmp_to_key

class Solution:
    def minDamage(self, power: int, damage: List[int], health: List[int]) -> int:
        enemies = []
        for h, d in zip(health, damage):
            turns = (h + power - 1) // power
            enemies.append((turns, d))
        
        def compare(a, b):
            turns_a, damage_a = a
            turns_b, damage_b = b
            
            left = damage_a * turns_b
            right = damage_b * turns_a
            
            if left > right:
                return -1
            if left < right:
                return 1
            return 0
        
        enemies.sort(key=cmp_to_key(compare))
        
        total_damage = 0
        time = 0
        
        for turns, d in enemies:
            time += turns
            total_damage += time * d
        
        return total_damage