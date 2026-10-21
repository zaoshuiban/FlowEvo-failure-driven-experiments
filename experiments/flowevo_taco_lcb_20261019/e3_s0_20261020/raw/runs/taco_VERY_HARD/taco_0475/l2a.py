import sys
from collections import deque


def build_order(n, sources):
    dist = [-1] * n
    q = deque()

    for s in sources:
        dist[s] = 0
        q.append(s)

    order = []

    while q:
        v = q.popleft()
        order.append(v)

        u = v - 1
        if u < 0:
            u = n - 1
        if dist[u] == -1:
            dist[u] = dist[v] + 1
            q.append(u)

        u = v + 1
        if u == n:
            u = 0
        if dist[u] == -1:
            dist[u] = dist[v] + 1
            q.append(u)

    return order


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1

    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        bad = [False] * n
        forced = []

        for i, val in enumerate(a):
            if (val | k) != k:
                bad[i] = True
                forced.append(i)

        if forced:
            independent = True

            for i in forced:
                nxt = i + 1
                if nxt == n:
                    nxt = 0
                if bad[nxt]:
                    independent = False
                    break

            if not independent:
                answers.append("-1")
                continue

            remaining_or = 0
            for i, val in enumerate(a):
                if not bad[i]:
                    remaining_or |= val

            if remaining_or != k:
                answers.append("-1")
                continue

            order = build_order(n, forced)
            answers.append(" ".join(str(pos + 1) for pos in order))

        else:
            total_or = 0
            for val in a:
                total_or |= val

            if total_or != k:
                answers.append("-1")
                continue

            pref = [0] * (n + 1)
            for i, val in enumerate(a):
                pref[i + 1] = pref[i] | val

            suffix_or = 0
            redundant = -1

            for i in range(n - 1, -1, -1):
                if (pref[i] | suffix_or) == k:
                    redundant = i
                    break
                suffix_or |= a[i]

            if redundant == -1:
                answers.append("-1")
            else:
                order = build_order(n, [redundant])
                answers.append(" ".join(str(pos + 1) for pos in order))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()