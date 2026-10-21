import sys


def on_leg(O, A, P):
    ox, oy = O
    ax, ay = A
    px, py = P

    ux = ax - ox
    uy = ay - oy
    wx = px - ox
    wy = py - oy

    if ux * wy - uy * wx != 0:
        return False

    length2 = ux * ux + uy * uy
    dot = ux * wx + uy * wy

    # The point must divide the segment in proportion at least 1/4.
    # If P = O + lambda * (A - O), this is equivalent to 1/5 <= lambda <= 4/5.
    return length2 <= 5 * dot <= 4 * length2


def check_legs(O, A, B, C, D):
    ux = A[0] - O[0]
    uy = A[1] - O[1]
    vx = B[0] - O[0]
    vy = B[1] - O[1]

    dot = ux * vx + uy * vy
    cross = ux * vy - uy * vx

    # 0 < angle <= 90 degrees:
    # not collinear, and dot product is non-negative.
    if cross == 0 or dot < 0:
        return False

    return (
        (on_leg(O, A, C) and on_leg(O, B, D))
        or
        (on_leg(O, A, D) and on_leg(O, B, C))
    )


def is_letter_A(segments):
    for i in range(3):
        for j in range(3):
            if i == j:
                continue

            k = 3 - i - j
            s1 = segments[i]
            s2 = segments[j]
            s3 = segments[k]

            for first_endpoint in (0, 1):
                O = s1[first_endpoint]
                A = s1[1 - first_endpoint]

                if O == s2[0]:
                    B = s2[1]
                    if check_legs(O, A, B, s3[0], s3[1]):
                        return True

                if O == s2[1]:
                    B = s2[0]
                    if check_legs(O, A, B, s3[0], s3[1]):
                        return True

    return False


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        segments = []
        for _ in range(3):
            x1, y1, x2, y2 = data[pos], data[pos + 1], data[pos + 2], data[pos + 3]
            pos += 4
            segments.append(((x1, y1), (x2, y2)))

        answers.append("YES" if is_letter_A(segments) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()