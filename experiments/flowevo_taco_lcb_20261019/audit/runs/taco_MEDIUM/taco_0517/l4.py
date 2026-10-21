import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    angles = data[2:2 + q]

    # hackonacci(n) modulo 2 satisfies:
    # h[n] = h[n-1] + h[n-3] (mod 2)
    h = [0] * 8
    h[1] = 1  # hackonacci(1) = 1 is odd
    h[2] = 0  # hackonacci(2) = 2 is even
    h[3] = 1  # hackonacci(3) = 3 is odd

    for i in range(4, 8):
        h[i] = (h[i - 1] + h[i - 3]) & 1

    # The parity sequence has period 7: h[1] ... h[7]
    parity_by_residue = [h[i] for i in range(1, 8)]

    # parity_for_product_mod[m] = parity of hackonacci((i*j)^2)
    # when (i*j) % 7 == m
    parity_for_product_mod = [0] * 7
    for m in range(7):
        exponent_mod = (m * m) % 7
        parity_for_product_mod[m] = parity_by_residue[(exponent_mod - 1) % 7]

    # value[r][c] is the cell value residue when row % 7 == r and col % 7 == c.
    # 1 means Y / odd, 0 means X / even.
    value = [[0] * 7 for _ in range(7)]
    for r in range(7):
        for c in range(7):
            value[r][c] = parity_for_product_mod[(r * c) % 7]

    # Frequencies of residues modulo 7 among indices 1..n
    freq = [0] * 7
    for i in range(1, n + 1):
        freq[i % 7] += 1

    base = (n + 1) % 7

    diff_90 = 0
    diff_180 = 0
    diff_270 = 0

    for r in range(7):
        if freq[r] == 0:
            continue

        for c in range(7):
            if freq[c] == 0:
                continue

            weight = freq[r] * freq[c]
            current = value[r][c]

            # 90 degrees clockwise:
            # new(i, j) = old(n + 1 - j, i)
            if current != value[(base - c) % 7][r]:
                diff_90 += weight

            # 180 degrees:
            # new(i, j) = old(n + 1 - i, n + 1 - j)
            if current != value[(base - r) % 7][(base - c) % 7]:
                diff_180 += weight

            # 270 degrees clockwise:
            # new(i, j) = old(j, n + 1 - i)
            if current != value[c][(base - r) % 7]:
                diff_270 += weight

    answers = []
    for angle in angles:
        angle %= 360

        if angle == 0:
            answers.append("0")
        elif angle == 90:
            answers.append(str(diff_90))
        elif angle == 180:
            answers.append(str(diff_180))
        else:  # angle == 270
            answers.append(str(diff_270))

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()