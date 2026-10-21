import sys
from array import array
from bisect import bisect_left

MOD = 998244353


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N, M, K = data[0], data[1], data[2]

    extras = []
    source_set = set()

    p = 3
    for _ in range(M):
        x = data[p] - 1
        y = data[p + 1] - 1
        p += 2
        extras.append((x, y))
        source_set.add(x)

    if M == 0:
        print(1)
        return

    sources = sorted(source_set)
    S = len(sources)
    pos_to_idx = {v: i for i, v in enumerate(sources)}

    out = [[] for _ in range(S)]
    incoming = [[] for _ in range(S)]

    # Base-cycle edges from each source
    for i, x in enumerate(sources):
        y = x + 1
        if y == N:
            y = 0

        j = bisect_left(sources, y)
        if j == S:
            dest_pos = sources[0] + N
            dest = 0
        else:
            dest_pos = sources[j]
            dest = j

        cost = 1 + (dest_pos - y)
        out[i].append((dest, cost))
        incoming[dest].append((i, cost))

    # Extra edges
    for x, y in extras:
        i = pos_to_idx[x]

        j = bisect_left(sources, y)
        if j == S:
            dest_pos = sources[0] + N
            dest = 0
        else:
            dest_pos = sources[j]
            dest = j

        cost = 1 + (dest_pos - y)
        out[i].append((dest, cost))
        incoming[dest].append((i, cost))

    # First source reached from vertex 0 by following the base cycle.
    arrival = 0 if sources[0] == 0 else sources[0]

    if arrival > K:
        print(1)
        return

    # dp[i][t]: number of ways to be at source i at time t,
    # just before choosing the next outgoing edge.
    dp = [array('I', [0]) * (K + 1) for _ in range(S)]
    dp[0][arrival] = 1

    incoming_ref = []
    for v in range(S):
        lst = []
        for u, cost in incoming[v]:
            if cost <= K:
                lst.append((dp[u], cost))
        incoming_ref.append(lst)

    # grt[i] is the number of outgoing choices from source i
    # that currently would finish before reaching the next source.
    grt = [0] * S
    activations = []

    for u in range(S):
        for _, cost in out[u]:
            activate_time = K - cost + 1
            if activate_time <= 0:
                grt[u] += 1
            elif activate_time < K:
                activations.append((activate_time, u))

    activations.sort()
    ptr = 0
    A = len(activations)

    ans = 0

    # Times 0, ..., K-1: after choosing an edge, some paths may finish
    # before reaching the next source.
    for t in range(K):
        while ptr < A and activations[ptr][0] <= t:
            grt[activations[ptr][1]] += 1
            ptr += 1

        for v in range(S):
            val = dp[v][t]

            for arr, cost in incoming_ref[v]:
                if cost <= t:
                    val += arr[t - cost]

            val %= MOD
            dp[v][t] = val
            ans += val * grt[v]

    # Time K: paths ending exactly at a source at time K are also valid.
    t = K
    for v in range(S):
        val = dp[v][t]

        for arr, cost in incoming_ref[v]:
            val += arr[t - cost]

        val %= MOD
        dp[v][t] = val
        ans += val

    print(ans % MOD)


if __name__ == "__main__":
    main()