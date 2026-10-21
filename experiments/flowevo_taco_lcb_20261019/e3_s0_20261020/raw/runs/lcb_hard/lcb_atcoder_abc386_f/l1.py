import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    K = int(data[0])
    S = data[1]
    T = data[2]

    n0 = len(S)
    m0 = len(T)

    # Remove common prefix.
    p = 0
    lim = min(n0, m0)
    while p < lim and S[p] == T[p]:
        p += 1

    # Remove common suffix.
    nrem = n0 - p
    mrem = m0 - p
    lim2 = min(nrem, mrem)

    suf = 0
    while suf < lim2 and S[n0 - 1 - suf] == T[m0 - 1 - suf]:
        suf += 1

    if p > 0 or suf > 0:
        S = S[p:n0 - suf]
        T = T[p:m0 - suf]

    n = len(S)
    m = len(T)

    if abs(n - m) > K:
        print("No")
        return

    if max(n, m) <= K:
        print("Yes")
        return

    if n == 0 or m == 0:
        print("No")
        return

    W = K
    INF = K + 1
    size = 2 * W + 3
    offset = W + 1

    prev = [INF] * size
    curr = [INF] * size

    prev_lower = 0
    prev_upper = min(W, m)

    # Row i = 0: dp[0][j] = j
    for d in range(prev_upper + 1):
        prev[d + offset] = d

    for i, s_char in enumerate(S, 1):
        if i <= W:
            lower = -i
        else:
            lower = -W

        upper = m - i
        if upper > W:
            upper = W

        pl = prev_lower
        pu = prev_upper

        for d in range(lower, upper + 1):
            idx = d + offset
            best = INF

            # Delete one character from S.
            dd = d + 1
            if pl <= dd <= pu:
                v = prev[dd + offset] + 1
                if v < best:
                    best = v

            # Insert one character into S.
            if d > lower:
                v = curr[idx - 1] + 1
                if v < best:
                    best = v

            # Replace or match.
            j = i + d
            if j > 0 and pl <= d <= pu:
                if s_char == T[j - 1]:
                    v = prev[idx]
                else:
                    v = prev[idx] + 1
                if v < best:
                    best = v

            curr[idx] = best

        prev, curr = curr, prev
        prev_lower = lower
        prev_upper = upper

    final_d = m - n
    ans = prev[final_d + offset]

    print("Yes" if ans <= K else "No")


if __name__ == "__main__":
    main()