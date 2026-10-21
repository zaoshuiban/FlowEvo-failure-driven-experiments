import sys
from functools import lru_cache

def main():
    input = sys.stdin.readline
    N, M = map(int, input().split())
    S = [input().strip() for _ in range(N)]

    adj = [0] * N
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            diff = sum(S[i][k] != S[j][k] for k in range(M))
            if diff == 1:
                adj[i] |= 1 << j

    @lru_cache(None)
    def dfs(mask, last):
        if mask == (1 << N) - 1:
            return True

        for nxt in range(N):
            if not (mask >> nxt) & 1 and (adj[last] >> nxt) & 1:
                if dfs(mask | (1 << nxt), nxt):
                    return True
        return False

    for start in range(N):
        if dfs(1 << start, start):
            print("Yes")
            return

    print("No")


if __name__ == "__main__":
    main()