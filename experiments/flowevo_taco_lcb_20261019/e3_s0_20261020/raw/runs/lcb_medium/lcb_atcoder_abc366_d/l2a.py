import sys

def main():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    nxt = it.__next__

    N = nxt()
    D = N + 1
    D2 = D * D

    P = [0] * (D * D * D)

    for x in range(1, N + 1):
        x_base = x * D2
        for y in range(1, N + 1):
            base = x_base + y * D
            base_x = base - D2
            base_y = base - D
            base_xy = base - D2 - D

            for z in range(1, D):
                a = nxt()
                idx = base + z
                P[idx] = (
                    a
                    + P[base_x + z]
                    + P[base_y + z]
                    + P[idx - 1]
                    - P[base_xy + z]
                    - P[base_x + z - 1]
                    - P[base_y + z - 1]
                    + P[base_xy + z - 1]
                )

    Q = nxt()
    answers = []
    append = answers.append

    for _ in range(Q):
        lx = nxt()
        rx = nxt()
        ly = nxt()
        ry = nxt()
        lz = nxt()
        rz = nxt()

        xl = (lx - 1) * D2
        xr = rx * D2
        yl = (ly - 1) * D
        yr = ry * D
        zl = lz - 1

        ans = (
            P[xr + yr + rz]
            - P[xl + yr + rz]
            - P[xr + yl + rz]
            - P[xr + yr + zl]
            + P[xl + yl + rz]
            + P[xl + yr + zl]
            + P[xr + yl + zl]
            - P[xl + yl + zl]
        )
        append(str(ans))

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")

if __name__ == "__main__":
    main()