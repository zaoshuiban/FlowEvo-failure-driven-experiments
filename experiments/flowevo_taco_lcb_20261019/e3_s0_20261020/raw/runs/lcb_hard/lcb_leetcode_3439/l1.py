from typing import List

class Solution:
    def minimumDiameterAfterMerge(self, edges1: List[List[int]], edges2: List[List[int]]) -> int:
        def get_diameter(edges: List[List[int]]) -> int:
            n = len(edges) + 1
            graph = [[] for _ in range(n)]
            
            for u, v in edges:
                graph[u].append(v)
                graph[v].append(u)
            
            def farthest(start: int):
                far_node = start
                max_dist = 0
                stack = [(start, -1, 0)]
                
                while stack:
                    node, parent, dist = stack.pop()
                    
                    if dist > max_dist:
                        max_dist = dist
                        far_node = node
                    
                    for nxt in graph[node]:
                        if nxt != parent:
                            stack.append((nxt, node, dist + 1))
                
                return far_node, max_dist
            
            endpoint, _ = farthest(0)
            _, diameter = farthest(endpoint)
            
            return diameter
        
        diameter1 = get_diameter(edges1)
        diameter2 = get_diameter(edges2)
        
        radius1 = (diameter1 + 1) // 2
        radius2 = (diameter2 + 1) // 2
        
        return max(diameter1, diameter2, radius1 + radius2 + 1)