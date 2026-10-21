import sys

INF = 10**9


def compute_best(Q, O, K):
    inf = INF
    no = len(O)

    p = 0
    r = 0
    prefix = inf

    dq = []
    head = 0

    res = []
    append = res.append

    for s, c in Q:
        while p < no and O[p][0] < s:
            oc = O[p][1]
            if oc < prefix:
                prefix = oc
            p += 1

        limit = s + K
        while r < no and O[r][0] <= limit:
            val = O[r][1]
            while len(dq) > head and O[dq[-1]][1] >= val:
                dq.pop()
            dq.append(r)
            r += 1

        while head < len(dq) and dq[head] < p:
            head += 1

        best = prefix

        if head < len(dq):
            v = O[dq[head]][1]
            if v < inf:
                v += 1
                if v < best:
                    best = v

        if c >= inf or best >= inf:
            append(inf)
        else:
            append(c + best)

    return res


def combine(A, B, K):
    la = len(A)
    lb = len(B)

    if la == 1 and lb == 1:
        s1, c1 = A[0]
        s2, c2 = B[0]
        base = c1 + c2

        if s1 > s2:
            cost1 = base
        elif s2 - s1 <= K:
            cost1 = base + 1
        else:
            cost1 = INF

        if s2 > s1:
            cost2 = base
        elif s1 - s2 <= K:
            cost2 = base + 1
        else:
            cost2 = INF

        if cost1 > INF:
            cost1 = INF
        if cost2 > INF:
            cost2 = INF

        if s1 < s2:
            return [(s1, cost1), (s2, cost2)]
        else:
            return [(s2, cost2), (s1, cost1)]

    ac = compute_best(A, B, K)
    bc = compute_best(B, A, K)

    res = []
    append = res.append

    i = j = 0

    while i < la and j < lb:
        if A[i][0] < B[j][0]:
            append((A[i][0], ac[i]))
            i += 1
        else:
            append((B[j][0], bc[j]))
            j += 1

    while i < la:
        append((A[i][0], ac[i]))
        i += 1

    while j < lb:
        append((B[j][0], bc[j]))
        j += 1

    return res


def solve_case(H, K, strengths):
    nodes = [[(s, 0)] for s in strengths]

    while len(nodes) > 1:
        new_nodes = []
        append = new_nodes.append

        for i in range(0, len(nodes), 2):
            append(combine(nodes[i], nodes[i + 1], K))

        nodes = new_nodes

    target = strengths[0]

    for s, c in nodes[0]:
        if s == target:
            return c if c < INF else -1

    return -1


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        H = data[idx]
        K = data[idx + 1]
        idx += 2

        N = 1 << H
        strengths = data[idx:idx + N]
        idx += N

        answers.append(str(solve_case(H, K, strengths)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()