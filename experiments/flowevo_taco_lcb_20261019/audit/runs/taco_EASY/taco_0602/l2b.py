import sys
from collections import deque

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    chars = ''.join(data[1:])

    total = n * n
    grid = [list(chars[i:i + n]) for i in range(0, total, n)]

    start = end = -1

    for i in range(n):
        for j in range(n):
            if grid[i][j] == 'S':
                start = i * n + j
            elif grid[i][j] == 'E':
                end = i * n + j

    dist = [-1] * total
    dist[start] = 0
    q = deque([start])

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while q:
        pos = q.popleft()

        if pos == end:
            print(dist[pos])
            return

        r, c = divmod(pos, n)

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if 0 <= nr < n and 0 <= nc < n:
                npos = nr * n + nc

                if grid[nr][nc] != 'T' and dist[npos] == -1:
                    dist[npos] = dist[pos] + 1
                    q.append(npos)

    print(-1)

if __name__ == "__main__":
    main()