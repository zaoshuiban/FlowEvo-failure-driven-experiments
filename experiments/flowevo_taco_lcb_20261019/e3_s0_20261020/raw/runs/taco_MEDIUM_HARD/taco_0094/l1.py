import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    s = data[1]
    t = data[2]

    parent = list(range(26))
    size = [1] * 26

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx = find(x)
        ry = find(y)
        if rx == ry:
            return False
        if size[rx] < size[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        size[rx] += size[ry]
        return True

    spells = []

    for a, b in zip(s, t):
        if a != b:
            x = ord(a) - ord('a')
            y = ord(b) - ord('a')
            if union(x, y):
                spells.append((a, b))

    output = [str(len(spells))]
    output.extend(f"{a} {b}" for a, b in spells)
    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()