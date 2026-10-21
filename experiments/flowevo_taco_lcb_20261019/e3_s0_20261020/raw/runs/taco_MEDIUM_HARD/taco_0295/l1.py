import sys


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    n = next_int()
    m = next_int()

    adj = [[] for _ in range(n + 1)]
    for _ in range(m):
        a = next_int()
        b = next_int()
        adj[a].append(b)
        adj[b].append(a)

    topic = [0] * (n + 1)
    for i in range(1, n + 1):
        topic[i] = next_int()

    data = b""

    mark = [0] * (n + 2)
    stamp = 0

    for v in range(1, n + 1):
        tv = topic[v]
        neighbors = adj[v]

        if tv > len(neighbors) + 1:
            sys.stdout.write("-1\n")
            return

        stamp += 1

        for u in neighbors:
            c = topic[u]
            if c <= tv:
                mark[c] = stamp

        cur = 1
        while mark[cur] == stamp:
            cur += 1

        if cur != tv:
            sys.stdout.write("-1\n")
            return

    order = list(range(1, n + 1))
    order.sort(key=topic.__getitem__)

    sys.stdout.write(" ".join(map(str, order)))
    sys.stdout.write("\n")


if __name__ == "__main__":
    solve()