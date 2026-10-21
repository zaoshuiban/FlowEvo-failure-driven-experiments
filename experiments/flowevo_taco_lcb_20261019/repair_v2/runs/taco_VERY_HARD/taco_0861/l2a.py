import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]

        if n <= 1:
            answers.append("0")
            continue

        mn = min(a)
        order = list(range(n))
        order.sort(key=a.__getitem__, reverse=True)

        parent = list(range(n))
        size = [0] * n
        active = bytearray(n)
        mark = [0] * n
        stamp = 1
        ans = 0

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx = find(x)
            ry = find(y)
            if rx == ry:
                return
            if size[rx] < size[ry]:
                rx, ry = ry, rx
            parent[ry] = rx
            size[rx] += size[ry]

        i = 0
        while i < n:
            h = a[order[i]]

            if h == mn:
                break

            j = i + 1
            while j < n and a[order[j]] == h:
                j += 1

            for k in range(i, j):
                p = order[k]
                active[p] = 1
                parent[p] = p
                size[p] = 1

            for k in range(i, j):
                p = order[k]
                if p > 0 and active[p - 1]:
                    union(p, p - 1)
                if p + 1 < n and active[p + 1]:
                    union(p, p + 1)

            count = 0
            for k in range(i, j):
                p = order[k]
                root = find(p)
                if mark[root] != stamp:
                    mark[root] = stamp
                    count += 1

            ans += count
            stamp += 1
            i = j

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()