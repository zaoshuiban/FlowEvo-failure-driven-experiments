import sys


def on_seg_ratio(P, O, X):
    vx = O[0] - P[0]
    vy = O[1] - P[1]
    wx = X[0] - P[0]
    wy = X[1] - P[1]

    # X must lie on the line P-O.
    if vx * wy - vy * wx != 0:
        return False

    d = wx * vx + wy * vy
    len2 = vx * vx + vy * vy

    # Parameter t = d / len2 must satisfy 1/5 <= t <= 4/5.
    return 5 * d >= len2 and 5 * d <= 4 * len2


def valid(segs):
    for c in range(3):
        i = (c + 1) % 3
        j = (c + 2) % 3

        si = segs[i]
        sj = segs[j]
        sc = segs[c]

        for P in si:
            if P == sj[0] or P == sj[1]:
                Oi = si[1] if si[0] == P else si[0]
                Oj = sj[1] if sj[0] == P else sj[0]

                v1x = Oi[0] - P[0]
                v1y = Oi[1] - P[1]
                v2x = Oj[0] - P[0]
                v2y = Oj[1] - P[1]

                # Angle must be > 0 and <= 90 degrees.
                cross = v1x * v2y - v1y * v2x
                dot = v1x * v2x + v1y * v2y

                if cross == 0 or dot < 0:
                    continue

                X, Y = sc

                if ((on_seg_ratio(P, Oi, X) and on_seg_ratio(P, Oj, Y)) or
                        (on_seg_ratio(P, Oi, Y) and on_seg_ratio(P, Oj, X))):
                    return True

    return False


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        segs = []
        for _ in range(3):
            x1 = data[idx]
            y1 = data[idx + 1]
            x2 = data[idx + 2]
            y2 = data[idx + 3]
            idx += 4
            segs.append(((x1, y1), (x2, y2)))

        answers.append("YES" if valid(segs) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()