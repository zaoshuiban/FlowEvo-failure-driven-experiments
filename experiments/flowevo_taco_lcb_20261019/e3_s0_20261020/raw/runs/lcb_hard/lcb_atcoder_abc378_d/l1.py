import sys

def main():
    input = sys.stdin.readline

    H, W, K = map(int, input().split())
    S = [input().strip() for _ in range(H)]

    cell_id = [[-1] * W for _ in range(H)]
    cells = []

    for i in range(H):
        for j in range(W):
            if S[i][j] == '.':
                cell_id[i][j] = len(cells)
                cells.append((i, j))

    n = len(cells)

    if K == 0:
        print(n)
        return

    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    adj = [[] for _ in range(n)]

    for idx, (i, j) in enumerate(cells):
        for di, dj in directions:
            ni = i + di
            nj = j + dj
            if 0 <= ni < H and 0 <= nj < W:
                nxt = cell_id[ni][nj]
                if nxt != -1:
                    adj[idx].append(nxt)

    bits = [1 << i for i in range(n)]

    sys.setrecursionlimit(1 << 20)

    def dfs(v, depth, visited):
        if depth == K:
            return 1

        result = 0
        next_depth = depth + 1

        for to in adj[v]:
            bit = bits[to]
            if (visited & bit) == 0:
                result += dfs(to, next_depth, visited | bit)

        return result

    answer = 0
    for start in range(n):
        answer += dfs(start, 0, bits[start])

    print(answer)


if __name__ == "__main__":
    main()