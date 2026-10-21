import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    k = [0] + data[1:1 + n]

    pos = 1 + n
    adj = [[] for _ in range(n + 1)]

    for _ in range(n - 1):
        u, v = data[pos], data[pos + 1]
        pos += 2
        adj[u].append(v)
        adj[v].append(u)

    s = data[pos]

    parent = [0] * (n + 1)
    parent[s] = -1
    order = [s]

    for v in order:
        for u in adj[v]:
            if u == parent[v]:
                continue
            parent[u] = v
            order.append(u)

    first = [0] * (n + 1)
    extra = [0] * (n + 1)
    answer = 0

    for v in reversed(order):
        values = []
        sum_extra = 0

        for u in adj[v]:
            if u == parent[v]:
                continue
            values.append(first[u])
            sum_extra += extra[u]

        values.sort(reverse=True)

        m = len(values)
        total_first = sum(values)
        count = m + sum_extra

        # first[v] = maximum edge-multiplicity sum in v's subtree,
        # including the edge from v to its parent, if that edge is used once.
        limit = k[v] - 1
        if limit > count:
            limit = count

        if limit <= 0:
            gain = 0
        elif limit <= m:
            gain = sum(values[:limit])
        else:
            gain = total_first + (limit - m)

        first[v] = 1 + gain

        e = k[v] - count - 1
        extra[v] = e if e > 0 else 0

        if v == s:
            limit = k[v]
            if limit > count:
                limit = count

            if limit <= 0:
                root_sum = 0
            elif limit <= m:
                root_sum = sum(values[:limit])
            else:
                root_sum = total_first + (limit - m)

            answer = 2 * root_sum

    print(answer)


if __name__ == "__main__":
    main()