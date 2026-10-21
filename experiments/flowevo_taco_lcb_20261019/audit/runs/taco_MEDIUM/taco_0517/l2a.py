import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    angles = data[2:2 + q]

    # For p = (i * j) mod 7, the cell is Y iff p^2 mod 7 is in {0, 1}.
    # Equivalently, p is in {0, 1, 6}.
    value = (1, 1, 0, 0, 0, 0, 1)

    row_patterns = []
    for r in range(7):
        row = bytearray(n)
        for j in range(n):
            c = (j + 1) % 7
            row[j] = value[(r * c) % 7]
        row_patterns.append(bytes(row))

    matrix = bytearray()
    for i in range(n):
        r = (i + 1) % 7
        matrix.extend(row_patterns[r])

    diff_90 = 0
    diff_180 = 0

    for i in range(n):
        base = i * n

        idx_90 = (n - 1) * n + i
        row_180 = (n - 1 - i) * n
        idx_180 = row_180 + n - 1

        for j in range(n):
            current = matrix[base + j]

            if current != matrix[idx_90]:
                diff_90 += 1

            if current != matrix[idx_180]:
                diff_180 += 1

            idx_90 -= n
            idx_180 -= 1

    answers = []
    for angle in angles:
        angle %= 360

        if angle == 0:
            answers.append("0")
        elif angle == 90 or angle == 270:
            answers.append(str(diff_90))
        else:  # angle == 180
            answers.append(str(diff_180))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()