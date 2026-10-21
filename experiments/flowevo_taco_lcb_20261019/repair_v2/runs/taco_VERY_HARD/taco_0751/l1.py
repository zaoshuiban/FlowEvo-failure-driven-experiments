import sys

MOD = 1_000_000_007


def build_transitions():
    # trans[xb][yb][kb][state] = list of (next_state, multiplicity, xor_bit_sum)
    trans = [[[[None for _ in range(8)] for _ in range(2)]
              for _ in range(2)] for _ in range(2)]

    for xb in range(2):
        for yb in range(2):
            for kb in range(2):
                for state in range(8):
                    tx = (state >> 2) & 1
                    ty = (state >> 1) & 1
                    less = state & 1

                    agg = {}

                    for bi in range(2):
                        if tx and bi > xb:
                            continue
                        ntx = 1 if (tx and bi == xb) else 0

                        for bj in range(2):
                            if ty and bj > yb:
                                continue
                            nty = 1 if (ty and bj == yb) else 0

                            xor_bit = bi ^ bj

                            if not less and xor_bit > kb:
                                continue

                            nless = less or (xor_bit < kb)
                            ns = (ntx << 2) | (nty << 1) | int(nless)

                            if ns in agg:
                                mult, vsum = agg[ns]
                                agg[ns] = (mult + 1, vsum + xor_bit)
                            else:
                                agg[ns] = (1, xor_bit)

                    trans[xb][yb][kb][state] = [
                        (ns, mult, vsum) for ns, (mult, vsum) in agg.items()
                    ]

    return trans


TRANS = build_transitions()


def prefix_sum(X, Y, K):
    """
    Sum of ((i xor j) + 1) over
    0 <= i <= X, 0 <= j <= Y, (i xor j) <= K.
    """
    if X < 0 or Y < 0 or K < 0:
        return 0

    cnt = [0] * 8
    sm = [0] * 8

    # state bits: tight_x, tight_y, already_less_than_K
    cnt[6] = 1  # tight_x = 1, tight_y = 1, less = 0

    for bit in range(30, -1, -1):
        xb = (X >> bit) & 1
        yb = (Y >> bit) & 1
        kb = (K >> bit) & 1

        table = TRANS[xb][yb][kb]

        ncnt = [0] * 8
        nsm = [0] * 8

        for state in range(8):
            c = cnt[state]
            if c == 0:
                continue

            ssum = sm[state]
            base = ssum * 2

            for ns, mult, vsum in table[state]:
                ncnt[ns] += c * mult
                nsm[ns] += base * mult + c * vsum

        cnt = ncnt
        sm = nsm

    result = 0
    for i in range(8):
        result += sm[i] + cnt[i]

    return result % MOD


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    q = data[0]

    idx = 1
    answers = []

    for _ in range(q):
        x1, y1, x2, y2, k = data[idx:idx + 5]
        idx += 5

        K = k - 1

        A = x1 - 1
        B = x2 - 1
        C = y1 - 1
        D = y2 - 1

        ans = (
            prefix_sum(B, D, K)
            - prefix_sum(A - 1, D, K)
            - prefix_sum(B, C - 1, K)
            + prefix_sum(A - 1, C - 1, K)
        ) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()