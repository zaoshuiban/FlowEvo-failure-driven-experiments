import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0

    N = data[idx]
    idx += 1

    W = [0] * (N + 1)
    for i in range(1, N + 1):
        W[i] = data[idx]
        idx += 1

    M = 2 * N + 2
    INF = 10**30

    L = [0] * (N + 1)
    R = [0] * (N + 1)

    min_by_l = [INF] * (M + 2)
    min_by_r = [INF] * (M + 2)

    for i in range(1, N + 1):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        L[i] = l
        R[i] = r
        w = W[i]

        if w < min_by_l[l]:
            min_by_l[l] = w
        if w < min_by_r[r]:
            min_by_r[r] = w

    Q = data[idx]
    idx += 1

    # prefix minimum by right endpoint
    prefix_r = [INF] * (M + 2)
    cur = INF
    for c in range(1, M + 1):
        if min_by_r[c] < cur:
            cur = min_by_r[c]
        prefix_r[c] = cur

    # suffix minimum by left endpoint
    suffix_l = [INF] * (M + 2)
    cur = INF
    for c in range(M, 0, -1):
        if min_by_l[c] < cur:
            cur = min_by_l[c]
        suffix_l[c] = cur

    # segment trees for range minimum queries
    size = 1
    while size < M:
        size <<= 1

    tree_l = [INF] * (2 * size)
    tree_r = [INF] * (2 * size)

    for c in range(1, M + 1):
        tree_l[size + c - 1] = min_by_l[c]
        tree_r[size + c - 1] = min_by_r[c]

    for i in range(size - 1, 0, -1):
        left = tree_l[i << 1]
        right = tree_l[i << 1 | 1]
        tree_l[i] = left if left < right else right

        left = tree_r[i << 1]
        right = tree_r[i << 1 | 1]
        tree_r[i] = left if left < right else right

    def range_min(tree, l, r):
        if l > r:
            return INF

        l += size - 1
        r += size - 1
        res = INF

        while l <= r:
            if l & 1:
                if tree[l] < res:
                    res = tree[l]
                l += 1

            if not (r & 1):
                if tree[r] < res:
                    res = tree[r]
                r -= 1

            l >>= 1
            r >>= 1

        return res

    answers = []

    for _ in range(Q):
        s = data[idx]
        t = data[idx + 1]
        idx += 2

        Ls, Rs = L[s], R[s]
        Lt, Rt = L[t], R[t]

        # Direct edge exists iff the intervals are disjoint.
        if Rs < Lt or Rt < Ls:
            answers.append(str(W[s] + W[t]))
            continue

        best = INF

        # Length-2 path: s -> u -> t
        min_left = Ls if Ls < Lt else Lt
        max_right = Rs if Rs > Rt else Rt

        if min_left > 1:
            if prefix_r[min_left - 1] < best:
                best = prefix_r[min_left - 1]

        if max_right + 1 <= M:
            if suffix_l[max_right + 1] < best:
                best = suffix_l[max_right + 1]

        # Length-3 path: s -> a -> b -> t
        # Case 1: s is shifted left relative to t.
        if Rs + 1 <= Rt and Ls <= Lt - 1:
            amin = range_min(tree_l, Rs + 1, Rt)
            if amin < INF:
                bmin = range_min(tree_r, Ls, Lt - 1)
                val = amin + bmin
                if val < best:
                    best = val

        # Case 2: t is shifted left relative to s.
        if Rt + 1 <= Rs and Lt <= Ls - 1:
            bmin = range_min(tree_l, Rt + 1, Rs)
            if bmin < INF:
                amin = range_min(tree_r, Lt, Ls - 1)
                val = amin + bmin
                if val < best:
                    best = val

        if best >= INF // 2:
            answers.append("-1")
        else:
            answers.append(str(W[s] + W[t] + best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()