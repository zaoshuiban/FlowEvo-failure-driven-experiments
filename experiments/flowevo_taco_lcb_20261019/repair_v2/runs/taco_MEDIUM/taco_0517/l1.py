import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    angles = data[2:2 + q]

    # For parity, hackonacci has period 7:
    # odd for indices congruent to 0, 1, 6 modulo 7 after squaring logic.
    good = [0] * 7
    good[0] = good[1] = good[6] = 1

    # Build repeating row patterns for i modulo 7.
    patterns = []
    for im in range(7):
        pat = bytearray(7)
        for jj in range(7):
            jres = (jj + 1) % 7
            pat[jj] = good[(im * jres) % 7]
        patterns.append(bytes(pat))

    # 1 = Y, 0 = X
    mat = bytearray(n * n)
    repeats = (n + 6) // 7

    for i in range(1, n + 1):
        row = (patterns[i % 7] * repeats)[:n]
        start = (i - 1) * n
        mat[start:start + n] = row

    ans90 = 0
    ans180 = 0

    for i in range(n):
        row_start = i * n
        opp_row_start = (n - 1 - i) * n

        for j in range(n):
            value = mat[row_start + j]

            # Rotation by 180 degrees
            if value != mat[opp_row_start + (n - 1 - j)]:
                ans180 += 1

            # Rotation by 90 degrees clockwise
            if value != mat[(n - 1 - j) * n + i]:
                ans90 += 1

    # For a square matrix, 90 and 270 degree rotations have the same
    # number of differing cells.
    ans270 = ans90

    rotation_answers = [0, ans90, ans180, ans270]

    output = []
    for angle in angles:
        output.append(str(rotation_answers[(angle % 360) // 90]))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()