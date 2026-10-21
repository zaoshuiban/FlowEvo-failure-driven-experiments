import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    parent = list(range(n))
    rank = [0] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra = find(a)
        rb = find(b)
        if ra == rb:
            return

        if rank[ra] < rank[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1

    idx = 2
    for _ in range(m):
        a = data[idx] - 1
        b = data[idx + 1] - 1
        idx += 2
        union(a, b)

    groups = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i + 1)

    triples = []
    pairs = []
    singles = []

    for component in groups.values():
        size = len(component)

        if size > 3:
            print(-1)
            return

        if size == 3:
            triples.append(component)
        elif size == 2:
            pairs.append(component)
        else:
            singles.append(component[0])

    if len(singles) < len(pairs) or (len(singles) - len(pairs)) % 3 != 0:
        print(-1)
        return

    teams = []

    for component in triples:
        teams.append(component)

    for component in pairs:
        single = singles.pop()
        teams.append([component[0], component[1], single])

    while singles:
        a = singles.pop()
        b = singles.pop()
        c = singles.pop()
        teams.append([a, b, c])

    output = [" ".join(map(str, team)) for team in teams]
    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()