import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)

    edges = []
    for _ in range(n - 1):
        u = next(it)
        v = next(it)
        edges.append((u, v))

    colors = [0] + [next(it) for _ in range(n)]

    bad_count = 0
    bad_incident = [0] * (n + 1)

    for u, v in edges:
        if colors[u] != colors[v]:
            bad_count += 1
            bad_incident[u] += 1
            bad_incident[v] += 1

    for v in range(1, n + 1):
        if bad_incident[v] == bad_count:
            print("YES")
            print(v)
            return

    print("NO")


if __name__ == "__main__":
    solve()