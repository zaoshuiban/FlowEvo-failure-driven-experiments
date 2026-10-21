import sys

def main():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    N = next(it)
    M = next(it)

    parent = [0] * (N + 1)
    for i in range(2, N + 1):
        parent[i] = next(it)

    INF_NEG = -10**9
    cover = [INF_NEG] * (N + 1)

    for _ in range(M):
        x = next(it)
        y = next(it)
        if y > cover[x]:
            cover[x] = y

    ans = 0

    for i in range(1, N + 1):
        if i > 1:
            inherited = cover[parent[i]] - 1
            if inherited > cover[i]:
                cover[i] = inherited

        if cover[i] >= 0:
            ans += 1

    print(ans)

if __name__ == "__main__":
    main()