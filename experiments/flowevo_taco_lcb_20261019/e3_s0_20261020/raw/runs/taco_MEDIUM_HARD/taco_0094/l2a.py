import sys

def solve() -> None:
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    s = data[1]
    t = data[2]

    parent = list(range(26))
    size = [1] * 26

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
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]

    for a, b in zip(s, t):
        if a != b:
            union(ord(a) - ord('a'), ord(b) - ord('a'))

    groups = {}
    for i in range(26):
        root = find(i)
        groups.setdefault(root, []).append(i)

    answer = []

    for component in groups.values():
        if len(component) > 1:
            base = component[0]
            for v in component[1:]:
                answer.append((chr(base + ord('a')), chr(v + ord('a'))))

    print(len(answer))
    for a, b in answer:
        print(a, b)


if __name__ == "__main__":
    solve()