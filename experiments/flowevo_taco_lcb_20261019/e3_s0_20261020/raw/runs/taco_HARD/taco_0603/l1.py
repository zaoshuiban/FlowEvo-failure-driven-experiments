import sys


def on_leg(A, B, P):
    vx = B[0] - A[0]
    vy = B[1] - A[1]

    wx = P[0] - A[0]
    wy = P[1] - A[1]

    # P must be collinear with segment AB.
    if vx * wy - vy * wx != 0:
        return False

    len2 = vx * vx + vy * vy
    dot = wx * vx + wy * vy

    # Parameter t = dot / len2 must satisfy 1/5 <= t <= 4/5
    return 5 * dot >= len2 and 5 * dot <= 4 * len2


def valid_A(A, B1, B2, C, D):
    ux = B1[0] - A[0]
    uy = B1[1] - A[1]

    vx = B2[0] - A[0]
    vy = B2[1] - A[1]

    dot = ux * vx + uy * vy
    cross = ux * vy - uy * vx

    # Angle must be in (0, 90].
    if dot < 0 or cross == 0:
        return False

    return (
        (on_leg(A, B1, C) and on_leg(A, B2, D)) or
        (on_leg(A, B1, D) and on_leg(A, B2, C))
    )


def possible(segments):
    for cross_idx in range(3):
        legs = [i for i in range(3) if i != cross_idx]

        s1 = segments[legs[0]]
        s2 = segments[legs[1]]
        C, D = segments[cross_idx]

        for i in range(2):
            for j in range(2):
                if s1[i] == s2[j]:
                    A = s1[i]
                    B1 = s1[1 - i]
                    B2 = s2[1 - j]

                    if valid_A(A, B1, B2, C, D):
                        return True

    return False


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        segments = []

        for _ in range(3):
            x1, y1, x2, y2 = data[pos:pos + 4]
            pos += 4
            segments.append(((x1, y1), (x2, y2)))

        answers.append("YES" if possible(segments) else "NO")

    print("\n".join(answers))


if __name__ == "__main__":
    main()