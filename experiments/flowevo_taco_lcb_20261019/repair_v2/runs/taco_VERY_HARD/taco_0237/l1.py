import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0

    m = data[idx]
    idx += 1
    n = data[idx]
    idx += 1

    a = data[idx:idx + m]
    idx += m

    b = data[idx:idx + n]
    idx += n

    edges = []
    total = 0

    for i in range(m):
        s = data[idx]
        idx += 1
        ai = a[i]

        for _ in range(s):
            j = data[idx] - 1
            idx += 1

            weight = ai + b[j]
            total += weight
            edges.append((weight, i, m + j))

    edges.sort(reverse=True)

    parent = list(range(m + n))
    size = [1] * (m + n)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    kept = 0

    for weight, u, v in edges:
        ru = find(u)
        rv = find(v)

        if ru != rv:
            if size[ru] < size[rv]:
                ru, rv = rv, ru

            parent[rv] = ru
            size[ru] += size[rv]
            kept += weight

    print(total - kept)


if __name__ == "__main__":
    solve()