from typing import List

class Solution:
    def stringIndices(self, wordsContainer: List[str], wordsQuery: List[str]) -> List[int]:
        lengths = [len(w) for w in wordsContainer]
        
        # Trie edges are stored as: key = (node << 5) + character
        nxt = {}
        
        # best[node] = best word index among all words passing through this node
        best = [-1]
        
        for i, word in enumerate(wordsContainer):
            word_len = lengths[i]
            node = 0
            
            current = best[0]
            if (
                current == -1
                or word_len < lengths[current]
                or (word_len == lengths[current] and i < current)
            ):
                best[0] = i
            
            for ch in reversed(word):
                c = ord(ch) - ord('a')
                key = (node << 5) + c
                child = nxt.get(key)
                
                if child is None:
                    child = len(best)
                    nxt[key] = child
                    best.append(-1)
                
                node = child
                current = best[node]
                
                if (
                    current == -1
                    or word_len < lengths[current]
                    or (word_len == lengths[current] and i < current)
                ):
                    best[node] = i
        
        answer = []
        
        for query in wordsQuery:
            node = 0
            
            for ch in reversed(query):
                c = ord(ch) - ord('a')
                key = (node << 5) + c
                child = nxt.get(key)
                
                if child is None:
                    break
                
                node = child
            
            answer.append(best[node])
        
        return answer