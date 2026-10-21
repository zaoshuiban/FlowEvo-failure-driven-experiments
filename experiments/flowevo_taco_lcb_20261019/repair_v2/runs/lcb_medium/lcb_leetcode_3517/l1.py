from typing import List
from collections import deque

class Solution:
    def shortestDistanceAfterQueries(self, n: int, queries: List[List[int]]) -> List[int]:
        graph = [[] for _ in range(n)]
        
        for i in range(n - 1):
            graph[i].append(i + 1)
        
        answer = []
        
        for u, v in queries:
            graph[u].append(v)
            
            dist = [-1] * n
            dist[0] = 0
            queue = deque([0])
            
            while queue:
                city = queue.popleft()
                
                if city == n - 1:
                    break
                
                for nxt in graph[city]:
                    if dist[nxt] == -1:
                        dist[nxt] = dist[city] + 1
                        queue.append(nxt)
            
            answer.append(dist[n - 1])
        
        return answer