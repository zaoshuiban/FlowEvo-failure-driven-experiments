import sys


def solve():
    input = sys.stdin.readline

    n_line = input()
    if not n_line:
        return

    n = int(n_line)
    s = input().strip()
    t = input().strip()

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

    answer = []

    for a, b in zip(s, t):
        u = ord(a) - ord('a')
        v = ord(b) - ord('a')

        if u != v and union(u, v):
            answer.append((a, b))

    output = [str(len(answer))]
    output.extend(f"{a} {b}" for a, b in answer)

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()