from typing import List

class Solution:
    def minValidStrings(self, words: List[str], target: str) -> int:
        trie = [{}]

        for word in words:
            node = 0
            for ch in word:
                nxt = trie[node].get(ch)
                if nxt is None:
                    nxt = len(trie)
                    trie[node][ch] = nxt
                    trie.append({})
                node = nxt

        n = len(target)
        max_len = [0] * n

        for i in range(n):
            node = 0
            j = i
            while j < n:
                nxt = trie[node].get(target[j])
                if nxt is None:
                    break
                node = nxt
                j += 1
            max_len[i] = j - i

        jumps = 0
        cur_end = 0
        farthest = 0

        for i in range(n):
            if i > cur_end:
                return -1

            farthest = max(farthest, i + max_len[i])

            if i == cur_end:
                jumps += 1
                cur_end = farthest
                if cur_end >= n:
                    return jumps

        return -1