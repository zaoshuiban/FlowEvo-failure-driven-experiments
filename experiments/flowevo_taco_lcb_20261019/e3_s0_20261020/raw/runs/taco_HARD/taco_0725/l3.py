import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    r = [next(it) for _ in range(n)]

    first_switch = [-1] * n

    parent = list(range(m))
    xor_to_parent = [0] * m
    size = [1] * m

    def find(x):
        if parent[x] == x:
            return x

        y = x
        path = []
        while parent[y] != y:
            path.append(y)
            y = parent[y]

        root = y

        for node in reversed(path):
            p = parent[node]
            if p != root:
                xor_to_parent[node] ^= xor_to_parent[p]
            parent[node] = root

        return root

    for switch in range(m):
        cnt = next(it)

        for _ in range(cnt):
            room = next(it) - 1

            if first_switch[room] == -1:
                first_switch[room] = switch
            else:
                a = first_switch[room]
                b = switch
                required = r[room] ^ 1

                ra = find(a)
                rb = find(b)

                if ra == rb:
                    if (xor_to_parent[a] ^ xor_to_parent[b]) != required:
                        print("NO")
                        return
                else:
                    d = required ^ xor_to_parent[a] ^ xor_to_parent[b]

                    if size[ra] < size[rb]:
                        parent[ra] = rb
                        xor_to_parent[ra] = d
                        size[rb] += size[ra]
                    else:
                        parent[rb] = ra
                        xor_to_parent[rb] = d
                        size[ra] += size[rb]

    print("YES")


if __name__ == "__main__":
    solve()