import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]

    idx = 2
    for _ in range(m):
        a = data[idx] - 1
        b = data[idx + 1] - 1
        idx += 2
        union(a, b)

    components = {}
    for i in range(n):
        root = find(i)
        components.setdefault(root, []).append(i + 1)

    teams = []
    pairs = []
    singles = []

    for comp in components.values():
        if len(comp) > 3:
            print(-1)
            return
        elif len(comp) == 3:
            teams.append(comp)
        elif len(comp) == 2:
            pairs.append(comp)
        else:
            singles.extend(comp)

    if len(singles) < len(pairs):
        print(-1)
        return

    single_idx = 0

    for pair in pairs:
        teams.append(pair + [singles[single_idx]])
        single_idx += 1

    remaining_singles = singles[single_idx:]

    if len(remaining_singles) % 3 != 0:
        print(-1)
        return

    for i in range(0, len(remaining_singles), 3):
        teams.append(remaining_singles[i:i + 3])

    output = []
    for team in teams:
        output.append(" ".join(map(str, team)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()