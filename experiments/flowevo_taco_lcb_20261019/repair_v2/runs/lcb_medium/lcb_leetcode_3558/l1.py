from typing import List
import heapq

class Solution:
    def findSafeWalk(self, grid: List[List[int]], health: int) -> bool:
        m, n = len(grid), len(grid[0])
        INF = 10**9
        dist = [[INF] * n for _ in range(m)]
        
        dist[0][0] = grid[0][0]
        pq = [(dist[0][0], 0, 0)]
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        while pq:
            cost, x, y = heapq.heappop(pq)
            
            if cost != dist[x][y]:
                continue
            
            if x == m - 1 and y == n - 1:
                return cost < health
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < m and 0 <= ny < n:
                    new_cost = cost + grid[nx][ny]
                    
                    if new_cost < dist[nx][ny]:
                        dist[nx][ny] = new_cost
                        heapq.heappush(pq, (new_cost, nx, ny))
        
        return dist[m - 1][n - 1] < health