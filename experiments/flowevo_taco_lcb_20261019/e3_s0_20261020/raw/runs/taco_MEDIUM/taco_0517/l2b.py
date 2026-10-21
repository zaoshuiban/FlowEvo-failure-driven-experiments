import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    angles = data[2:2 + q]

    # F[r][c] is 1 if the cell is Y, 0 if X, where row mod 7 = r and column mod 7 = c.
    good_residues = {0, 1, 6}
    F = [[0] * 7 for _ in range(7)]
    for r in range(7):
        for c in range(7):
            if (r * c) % 7 in good_residues:
                F[r][c] = 1

    rem = [i % 7 for i in range(n + 1)]
    rev = [(n + 1 - i) % 7 for i in range(n + 1)]

    diff_90 = 0
    diff_180 = 0

    for i in range(1, n + 1):
        ri = rem[i]
        row = F[ri]
        row_180 = F[rev[i]]

        for j in range(1, n + 1):
            value = row[rem[j]]

            # Clockwise 90 / 270 degrees
            if value != row[rev[j]]:
                diff_90 += 1

            # 180 degrees
            if value != row_180[rev[j]]:
                diff_180 += 1

    answers = []
    for angle in angles:
        angle %= 360

        if angle == 0:
            answers.append("0")
        elif angle == 180:
            answers.append(str(diff_180))
        else:
            answers.append(str(diff_90))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()