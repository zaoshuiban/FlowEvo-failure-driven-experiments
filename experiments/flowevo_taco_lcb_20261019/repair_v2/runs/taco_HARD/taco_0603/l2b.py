import sys


def cross_vec(ax, ay, bx, by):
    return ax * by - ay * bx


def dist2(p, q):
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    return dx * dx + dy * dy


def on_segment(a, b, p):
    vx = b[0] - a[0]
    vy = b[1] - a[1]
    wx = p[0] - a[0]
    wy = p[1] - a[1]

    if vx * wy - vy * wx != 0:
        return False

    dot = vx * wx + vy * wy
    if dot < 0:
        return False

    len2 = vx * vx + vy * vy
    return dot <= len2


def ratio_ok(a, b, p):
    ap2 = dist2(a, p)
    pb2 = dist2(p, b)

    if ap2 == 0 or pb2 == 0:
        return False

    return 16 * ap2 >= pb2 and 16 * pb2 >= ap2


def on_leg_ok(a, b, p):
    return on_segment(a, b, p) and ratio_ok(a, b, p)


def angle_ok(a, b, c):
    vx = b[0] - a[0]
    vy = b[1] - a[1]
    wx = c[0] - a[0]
    wy = c[1] - a[1]

    dot = vx * wx + vy * wy
    cr = vx * wy - vy * wx

    return dot >= 0 and cr != 0


def pair_ok(leg1, leg2, crossbar):
    for a in (leg1[0], leg1[1]):
        if a == leg2[0] or a == leg2[1]:
            b = leg1[1] if a == leg1[0] else leg1[0]
            c = leg2[1] if a == leg2[0] else leg2[0]

            if not angle_ok(a, b, c):
                continue

            p, q = crossbar

            if (on_leg_ok(a, b, p) and on_leg_ok(a, c, q)) or \
               (on_leg_ok(a, b, q) and on_leg_ok(a, c, p)):
                return True

    return False


def check(segments):
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            k = 3 - i - j
            if pair_ok(segments[i], segments[j], segments[k]):
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
        segments = []
        for _ in range(3):
            x1, y1, x2, y2 = data[idx], data[idx + 1], data[idx + 2], data[idx + 3]
            idx += 4
            segments.append(((x1, y1), (x2, y2)))

        answers.append("YES" if check(segments) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()