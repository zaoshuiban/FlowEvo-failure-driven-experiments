import sys
from bisect import bisect_left


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    ptr = 1
    answers = []
    INF = 10**18

    for _ in range(t):
        s1 = data[ptr]
        s2 = data[ptr + 1]
        ptr += 2

        # Keep s1 as the longer string, so n - 1 >= m - 1
        if len(s1) < len(s2):
            s1, s2 = s2, s1

        n = len(s1)
        m = len(s2)

        pos1 = [[] for _ in range(26)]
        pos2 = [[] for _ in range(26)]

        for idx, ch in enumerate(s1):
            pos1[ch - 65].append(idx)

        for idx, ch in enumerate(s2):
            pos2[ch - 65].append(idx)

        A = n - 1
        B = m - 1
        P = A - B

        best_d = INF

        for c in range(26):
            X = pos1[c]
            Y = pos2[c]

            if not X or not Y:
                continue

            ylen = len(Y)

            for i in X:
                # We need to minimize:
                # dist(j, [B-i, A-i]) + dist(j, [i-P, i])
                l1 = B - i
                r1 = A - i
                l2 = i - P
                r2 = i

                # Left endpoint of the interval where this convex function is minimized
                if r1 < l2:
                    L = r1
                elif r2 < l1:
                    L = r2
                else:
                    L = l1 if l1 > l2 else l2

                k = bisect_left(Y, L)

                if k < ylen:
                    j = Y[k]

                    if j < l1:
                        d1 = l1 - j
                    elif j > r1:
                        d1 = j - r1
                    else:
                        d1 = 0

                    if j < l2:
                        d2 = l2 - j
                    elif j > r2:
                        d2 = j - r2
                    else:
                        d2 = 0

                    cur = d1 + d2
                    if cur < best_d:
                        best_d = cur
                        if best_d == 0:
                            break

                if k > 0:
                    j = Y[k - 1]

                    if j < l1:
                        d1 = l1 - j
                    elif j > r1:
                        d1 = j - r1
                    else:
                        d1 = 0

                    if j < l2:
                        d2 = l2 - j
                    elif j > r2:
                        d2 = j - r2
                    else:
                        d2 = 0

                    cur = d1 + d2
                    if cur < best_d:
                        best_d = cur
                        if best_d == 0:
                            break

            if best_d == 0:
                break

        answer = 2 * (P + best_d)
        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()