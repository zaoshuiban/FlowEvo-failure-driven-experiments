import sys

def main() -> None:
    input = sys.stdin.buffer.readline

    N = int(input())
    M = N + 1
    M2 = M * M

    pref = [0] * (M * M * M)

    for x in range(1, N + 1):
        x_base = x * M2
        for y in range(1, N + 1):
            values = list(map(int, input().split()))
            base = x_base + y * M

            for z, a in enumerate(values, 1):
                idx = base + z
                pref[idx] = (
                    a
                    + pref[idx - M2]
                    + pref[idx - M]
                    + pref[idx - 1]
                    - pref[idx - M2 - M]
                    - pref[idx - M2 - 1]
                    - pref[idx - M - 1]
                    + pref[idx - M2 - M - 1]
                )

    Q = int(input())
    answers = []
    p = pref

    for _ in range(Q):
        lx, rx, ly, ry, lz, rz = map(int, input().split())

        xr = rx * M2
        xl = (lx - 1) * M2
        yr = ry * M
        yl = (ly - 1) * M
        zr = rz
        zl = lz - 1

        ans = p[xr + yr + zr]
        ans -= p[xl + yr + zr]
        ans -= p[xr + yl + zr]
        ans -= p[xr + yr + zl]
        ans += p[xl + yl + zr]
        ans += p[xl + yr + zl]
        ans += p[xr + yl + zl]
        ans -= p[xl + yl + zl]

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()