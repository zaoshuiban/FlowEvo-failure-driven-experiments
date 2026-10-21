import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1
    m = data[idx]
    idx += 1

    status = [0] * (n + 1)
    for i in range(1, n + 1):
        status[i] = data[idx]
        idx += 1

    first = [0] * (n + 1)

    parent = list(range(m + 1))
    size = [1] * (m + 1)
    parity = [0] * (m + 1)

    sys.setrecursionlimit(1_000_000)

    def find(x):
        if parent[x] != x:
            p = parent[x]
            parent[x] = find(p)
            parity[x] ^= parity[p]
        return parent[x]

    possible = True

    for switch in range(1, m + 1):
        count = data[idx]
        idx += 1

        for _ in range(count):
            room = data[idx]
            idx += 1

            if first[room] == 0:
                first[room] = switch
            else:
                u = first[room]
                v = switch
                required = 1 - status[room]

                ru = find(u)
                pu = parity[u]

                rv = find(v)
                pv = parity[v]

                if ru == rv:
                    if (pu ^ pv) != required:
                        possible = False
                else:
                    if size[ru] < size[rv]:
                        parent[ru] = rv
                        parity[ru] = pu ^ pv ^ required
                        size[rv] += size[ru]
                    else:
                        parent[rv] = ru
                        parity[rv] = pu ^ pv ^ required
                        size[ru] += size[rv]

    print("YES" if possible else "NO")


if __name__ == "__main__":
    solve()