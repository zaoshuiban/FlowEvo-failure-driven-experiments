import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    parent = list(range(n + 1))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    idx = 2
    for _ in range(m):
        a, b = data[idx], data[idx + 1]
        idx += 2
        union(a, b)

    components = {}
    for v in range(1, n + 1):
        root = find(v)
        components.setdefault(root, []).append(v)

    singletons = []
    pairs = []
    triples = []

    for comp in components.values():
        size = len(comp)
        if size == 1:
            singletons.append(comp[0])
        elif size == 2:
            pairs.append(comp)
        elif size == 3:
            triples.append(comp)
        else:
            print(-1)
            return

    if len(singletons) < len(pairs):
        print(-1)
        return

    teams = []

    for comp in triples:
        teams.append(comp)

    for comp in pairs:
        v = singletons.pop()
        teams.append([comp[0], comp[1], v])

    if len(singletons) % 3 != 0:
        print(-1)
        return

    while singletons:
        teams.append([
            singletons.pop(),
            singletons.pop(),
            singletons.pop()
        ])

    output = [" ".join(map(str, team)) for team in teams]
    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()