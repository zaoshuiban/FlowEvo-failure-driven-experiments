import sys
from bisect import bisect_left, bisect_right

INF = 10**18


def minimum_extra(A, B, n, m):
    # Iterate over the smaller position list for speed.
    if len(A) > len(B):
        A, B = B, A
        n, m = m, n

    p = n - 1
    q = m - 1
    diff = n - m

    if diff >= 0:
        Ld, Rd = 0, diff
    else:
        Ld, Rd = diff, 0

    if p <= q:
        Ls, Rs = p, q
    else:
        Ls, Rs = q, p

    best = INF
    blen = len(B)
    bisl = bisect_left
    bisr = bisect_right

    for a in A:
        for dside in range(3):
            if dside == 0:  # a - b < Ld
                lo1 = a - Ld + 1
                hi1 = INF
                ca1, cb1, cc1 = -1, 1, Ld
            elif dside == 1:  # Ld <= a - b <= Rd
                lo1 = a - Rd
                hi1 = a - Ld
                ca1, cb1, cc1 = 0, 0, 0
            else:  # a - b > Rd
                lo1 = -INF
                hi1 = a - Rd - 1
                ca1, cb1, cc1 = 1, -1, -Rd

            for sside in range(3):
                if sside == 0:  # a + b < Ls
                    lo2 = -INF
                    hi2 = Ls - a - 1
                    ca2, cb2, cc2 = -1, -1, Ls
                elif sside == 1:  # Ls <= a + b <= Rs
                    lo2 = Ls - a
                    hi2 = Rs - a
                    ca2, cb2, cc2 = 0, 0, 0
                else:  # a + b > Rs
                    lo2 = Rs - a + 1
                    hi2 = INF
                    ca2, cb2, cc2 = 1, 1, -Rs

                lo = max(lo1, lo2)
                hi = min(hi1, hi2)

                if lo > hi:
                    continue

                left = bisl(B, lo)
                right = bisr(B, hi)

                if left >= right:
                    continue

                cb = cb1 + cb2

                if cb > 0:
                    b = B[left]
                elif cb < 0:
                    b = B[right - 1]
                else:
                    b = B[left]

                value = (ca1 + ca2) * a + cb * b + (cc1 + cc2)

                if value < best:
                    best = value
                    if best == 0:
                        return 0

    return best


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        s1 = data[idx]
        idx += 1
        s2 = data[idx]
        idx += 1

        n = len(s1)
        m = len(s2)

        pos1 = [[] for _ in range(26)]
        pos2 = [[] for _ in range(26)]

        for i, ch in enumerate(s1):
            pos1[ch - 65].append(i)

        for j, ch in enumerate(s2):
            pos2[ch - 65].append(j)

        min_extra = INF

        for c in range(26):
            A = pos1[c]
            B = pos2[c]

            if A and B:
                cur = minimum_extra(A, B, n, m)
                if cur < min_extra:
                    min_extra = cur
                    if min_extra == 0:
                        break

        answer = 2 * (abs(n - m) + min_extra)
        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()