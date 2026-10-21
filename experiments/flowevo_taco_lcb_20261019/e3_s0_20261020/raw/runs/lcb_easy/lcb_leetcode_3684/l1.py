class Solution:
    def hasMatch(self, s: str, p: str) -> bool:
        left, right = p.split('*')
        left_pos = s.find(left)
        if left_pos == -1:
            return False
        return s.find(right, left_pos + len(left)) != -1