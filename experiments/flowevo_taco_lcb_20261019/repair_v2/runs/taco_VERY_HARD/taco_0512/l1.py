import sys
import math

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    vals = data[1:]
    max_val = max(vals) if vals else 1

    # tau[n] = number of positive divisors of n
    tau = [0] * (max_val + 1)
    for d in range(1, max_val + 1):
        for multiple in range(d, max_val + 1, d):
            tau[multiple] += 1

    perms = [
        (0, 1, 2),
        (0, 2, 1),
        (1, 0, 2),
        (1, 2, 0),
        (2, 0, 1),
        (2, 1, 0)
    ]

    # Precompute inclusion-exclusion terms for the union of the 6 orientations.
    coeff = {}
    for mask in range(1, 1 << 6):
        sign = 1 if mask.bit_count() % 2 == 1 else -1
        bm = [0, 0, 0]

        for idx, p in enumerate(perms):
            if mask & (1 << idx):
                bm[0] |= 1 << p[0]
                bm[1] |= 1 << p[1]
                bm[2] |= 1 << p[2]

        key = (bm[0], bm[1], bm[2])
        coeff[key] = coeff.get(key, 0) + sign

    terms = [(c, x, y, z) for (x, y, z), c in coeff.items() if c]

    gcd = math.gcd
    cache = {}
    answers = []

    pos = 1
    for _ in range(t):
        A, B, C = data[pos], data[pos + 1], data[pos + 2]
        pos += 3

        # The answer is symmetric in A, B, C.
        if A > B:
            A, B = B, A
        if B > C:
            B, C = C, B
        if A > B:
            A, B = B, A

        key = (A, B, C)
        ans = cache.get(key)

        if ans is None:
            g3 = gcd(A, B)
            g5 = gcd(A, C)
            g6 = gcd(B, C)
            g7 = gcd(g3, C)

            tg = [0] * 8
            tg[1] = tau[A]
            tg[2] = tau[B]
            tg[4] = tau[C]
            tg[3] = tau[g3]
            tg[5] = tau[g5]
            tg[6] = tau[g6]
            tg[7] = tau[g7]

            # Number of ordered triples whose multiset can be matched
            # to the three sides of the box.
            ordered = 0
            for c, m0, m1, m2 in terms:
                ordered += c * tg[m0] * tg[m1] * tg[m2]

            tg_all = tg[7]

            tA = tg[1]
            tB = tg[2]
            tC = tg[4]
            tBC = tg[6]
            tAC = tg[5]
            tAB = tg[3]

            # Number of matchable multisets with exactly two equal elements.
            n2 = (
                tBC * tA + tAC * tB + tAB * tC
                - tg_all * (tBC + tAC + tAB)
                + tg_all * (tg_all - 1)
            )

            # Burnside / orbit correction:
            # ordered = n1 + 3*n2 + 6*n3
            ans = (ordered + 5 * tg_all + 3 * n2) // 6
            cache[key] = ans

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()