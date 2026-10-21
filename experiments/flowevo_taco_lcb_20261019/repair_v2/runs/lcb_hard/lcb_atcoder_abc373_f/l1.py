import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    N = next(it)
    W = next(it)

    NEG = -10**30
    dp = [NEG] * (W + 1)
    dp[0] = 0

    # Arrays for the convex hull trick
    qt = [0] * (W + 2)
    qb = [0] * (W + 2)

    for _ in range(N):
        w = next(it)
        v = next(it)

        ndp = dp.copy()

        # Small f(k) = k*v - k^2, used for small q
        fk = [0] * 7
        for k in range(1, 7):
            fk[k] = k * v - k * k

        # Only residues r with q >= 1 can receive an item of this type
        rmax = min(w - 1, W - w)

        for r in range(rmax + 1):
            Q = (W - r) // w

            if Q <= 6:
                idx = r
                for q in range(1, Q + 1):
                    idx += w
                    best = dp[idx]  # choose 0 items of this type

                    prev_idx = idx
                    for k in range(1, q + 1):
                        prev_idx -= w
                        prev = dp[prev_idx]
                        if prev != NEG:
                            cand = prev + fk[k]
                            if cand > best:
                                best = cand

                    if best > ndp[idx]:
                        ndp[idx] = best

            else:
                head = 0
                tail = 0

                val0 = dp[r]
                if val0 != NEG:
                    qt[0] = 0
                    qb[0] = val0
                    tail = 1

                idx = r

                for q in range(1, Q + 1):
                    idx += w
                    val = dp[idx]

                    qq = q * q
                    vq = v * q

                    if val != NEG:
                        # Line for t = q:
                        # value(x) = 2*t*x + (dp[t] - t^2 - v*t)
                        b = val - qq - vq

                        while tail - head >= 2:
                            t1 = qt[tail - 2]
                            b1 = qb[tail - 2]
                            t2 = qt[tail - 1]
                            b2 = qb[tail - 1]

                            if (b1 - b2) * (q - t2) >= (b2 - b) * (t2 - t1):
                                tail -= 1
                            else:
                                break

                        qt[tail] = q
                        qb[tail] = b
                        tail += 1

                    if head < tail:
                        while head + 1 < tail:
                            diff = qt[head + 1] - qt[head]
                            if qb[head] - qb[head + 1] <= 2 * q * diff:
                                head += 1
                            else:
                                break

                        best = 2 * qt[head] * q + qb[head]
                        nv = vq - qq + best

                        if nv > ndp[idx]:
                            ndp[idx] = nv

        dp = ndp

    print(max(dp))


if __name__ == "__main__":
    solve()