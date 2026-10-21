from typing import List

class Solution:
    def minimizeConcatenatedLength(self, words: List[str]) -> int:
        INF = 10**18
        
        first_char = ord(words[0][0]) - ord('a')
        last_char = ord(words[0][-1]) - ord('a')
        
        dp = [[INF] * 26 for _ in range(26)]
        dp[first_char][last_char] = len(words[0])
        
        for word in words[1:]:
            w_first = ord(word[0]) - ord('a')
            w_last = ord(word[-1]) - ord('a')
            w_len = len(word)
            
            ndp = [[INF] * 26 for _ in range(26)]
            
            for left in range(26):
                for right in range(26):
                    cur_len = dp[left][right]
                    if cur_len == INF:
                        continue
                    
                    # join(current_string, word)
                    new_len = cur_len + w_len - (1 if right == w_first else 0)
                    ndp[left][w_last] = min(ndp[left][w_last], new_len)
                    
                    # join(word, current_string)
                    new_len = cur_len + w_len - (1 if w_last == left else 0)
                    ndp[w_first][right] = min(ndp[w_first][right], new_len)
            
            dp = ndp
        
        return min(min(row) for row in dp)