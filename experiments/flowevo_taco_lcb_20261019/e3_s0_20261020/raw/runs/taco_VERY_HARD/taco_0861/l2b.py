import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        n = data[pos]
        pos += 1

        a = data[pos:pos + n]
        pos += n

        if n <= 1:
            answers.append("0")
            continue

        minimum = min(a)

        order = list(range(n))
        order.sort(key=a.__getitem__, reverse=True)

        parent = list(range(n))
        size = [1] * n
        active = bytearray(n)
        mark = [-1] * n
        epoch = 0

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

        answer = 0
        i = 0

        while i < n:
            value = a[order[i]]

            if value == minimum:
                break

            j = i + 1
            while j < n and a[order[j]] == value:
                j += 1

            for k in range(i, j):
                active[order[k]] = 1

            for k in range(i, j):
                idx = order[k]

                if idx > 0 and active[idx - 1]:
                    union(idx, idx - 1)

                if idx + 1 < n and active[idx + 1]:
                    union(idx, idx + 1)

            epoch += 1
            components = 0

            for k in range(i, j):
                root = find(order[k])
                if mark[root] != epoch:
                    mark[root] = epoch
                    components += 1

            answer += components
            i = j

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()