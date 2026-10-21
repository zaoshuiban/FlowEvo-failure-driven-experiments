import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ptr = 1
    answers = []

    for _ in range(t):
        n = data[ptr]
        ptr += 1

        a = data[ptr:ptr + n]
        ptr += n

        order = list(range(n))
        order.sort(key=a.__getitem__, reverse=True)

        parent = [-1] * n
        size = [1] * n
        mark = [0] * n

        def find(x, parent=parent):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        total = 0
        stamp = 0
        p = 0

        while p < n:
            value = a[order[p]]
            q = p + 1
            while q < n and a[order[q]] == value:
                q += 1

            for k in range(p, q):
                idx = order[k]
                parent[idx] = idx
                size[idx] = 1

            for k in range(p, q):
                idx = order[k]

                if idx > 0 and parent[idx - 1] != -1:
                    ra = find(idx)
                    rb = find(idx - 1)
                    if ra != rb:
                        if size[ra] < size[rb]:
                            ra, rb = rb, ra
                        parent[rb] = ra
                        size[ra] += size[rb]

                if idx + 1 < n and parent[idx + 1] != -1:
                    ra = find(idx)
                    rb = find(idx + 1)
                    if ra != rb:
                        if size[ra] < size[rb]:
                            ra, rb = rb, ra
                        parent[rb] = ra
                        size[ra] += size[rb]

            stamp += 1
            components = 0

            for k in range(p, q):
                root = find(order[k])
                if mark[root] != stamp:
                    mark[root] = stamp
                    components += 1

            total += components
            p = q

        answers.append(str(total - 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()