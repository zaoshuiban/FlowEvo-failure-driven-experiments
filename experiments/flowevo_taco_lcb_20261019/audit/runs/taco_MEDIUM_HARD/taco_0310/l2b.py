import sys


def balanced_forest(c, edges):
    n = len(c)

    adj = [[] for _ in range(n)]
    for x, y in edges:
        adj[x].append(y)
        adj[y].append(x)

    parent = [-1] * n
    parent[0] = -2
    order = []
    stack = [0]

    while stack:
        u = stack.pop()
        order.append(u)
        for v in adj[u]:
            if v == parent[u]:
                continue
            parent[v] = u
            stack.append(v)

    parent[0] = -1

    sub = c[:]
    for u in reversed(order):
        p = parent[u]
        if p != -1:
            sub[p] += sub[u]

    total = sub[0]

    freq = {}
    for u in range(1, n):
        s = sub[u]
        freq[s] = freq.get(s, 0) + 1

    INF = 10**30
    ans = INF

    # Cut the newly added edge and one original edge.
    if total % 2 == 0:
        half = total // 2
        if freq.get(half, 0) > 0:
            ans = min(ans, half)

    # Two disjoint subtrees have equal sums.
    for s, count in freq.items():
        if count >= 2 and 3 * s > total:
            ans = min(ans, 3 * s - total)

    anc_count = {}
    stack = [(0, 0)]  # node, state: 0 = enter, 1 = exit

    while stack:
        u, state = stack.pop()

        if state == 0:
            if u != 0:
                s = sub[u]

                # Ancestor cuts where s is one of the two equal larger parts.
                if 3 * s > total:
                    if anc_count.get(2 * s, 0) > 0 or anc_count.get(total - s, 0) > 0:
                        ans = min(ans, 3 * s - total)

                # s is the smaller component in an ancestor-related cut.
                elif 3 * s < total:
                    if (total + s) % 2 == 0:
                        target = (total + s) // 2
                        if anc_count.get(target, 0) > 0:
                            ans = min(ans, (total - 3 * s) // 2)

                    # A disjoint smaller subtree and another subtree equal to the remaining part.
                    if (total - s) % 2 == 0:
                        target = (total - s) // 2
                        if freq.get(target, 0) - anc_count.get(target, 0) > 0:
                            ans = min(ans, (total - 3 * s) // 2)

            stack.append((u, 1))

            if u != 0:
                s = sub[u]
                anc_count[s] = anc_count.get(s, 0) + 1

            for v in adj[u]:
                if v != parent[u]:
                    stack.append((v, 0))

        else:
            if u != 0:
                s = sub[u]
                anc_count[s] -= 1
                if anc_count[s] == 0:
                    del anc_count[s]

    return -1 if ans == INF else ans


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    q = data[idx]
    idx += 1

    answers = []

    for _ in range(q):
        n = data[idx]
        idx += 1

        c = data[idx:idx + n]
        idx += n

        edges = []
        for _ in range(n - 1):
            x = data[idx] - 1
            y = data[idx + 1] - 1
            idx += 2
            edges.append((x, y))

        answers.append(str(balanced_forest(c, edges)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()