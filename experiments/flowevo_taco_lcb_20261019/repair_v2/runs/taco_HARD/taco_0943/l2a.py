import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0

    n = data[idx]
    idx += 1

    a = [0] + data[idx:idx + n]
    idx += n

    parent = [0] * (n + 1)
    weight = [0] * (n + 1)
    children = [[] for _ in range(n + 1)]

    for v in range(2, n + 1):
        p = data[idx]
        w = data[idx + 1]
        idx += 2

        parent[v] = p
        weight[v] = w
        children[p].append(v)

    del data

    pref = [0] * (n + 1)
    order = [1]
    pos = 0

    while pos < len(order):
        v = order[pos]
        pos += 1

        for to in children[v]:
            pref[to] = pref[v] + weight[to]
            order.append(to)

    LOG = (n + 1).bit_length()
    up = [parent]

    for _ in range(1, LOG):
        prev = up[-1]
        cur = [0] * (n + 1)

        for v in range(1, n + 1):
            cur[v] = prev[prev[v]]

        up.append(cur)

    diff = [0] * (n + 1)

    for u in range(1, n + 1):
        target = pref[u] - a[u]
        cur = u

        for k in range(LOG - 1, -1, -1):
            anc = up[k][cur]
            if anc and pref[anc] >= target:
                cur = anc

        x = cur

        if x != u:
            p = parent[u]
            diff[p] += 1

            px = parent[x]
            if px:
                diff[px] -= 1

    for v in reversed(order):
        p = parent[v]
        if p:
            diff[p] += diff[v]

    sys.stdout.write(" ".join(str(diff[i]) for i in range(1, n + 1)))


if __name__ == "__main__":
    main()