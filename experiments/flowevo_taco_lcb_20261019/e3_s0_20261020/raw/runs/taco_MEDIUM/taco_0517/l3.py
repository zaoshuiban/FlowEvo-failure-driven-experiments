import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    angles = data[2:2 + q]

    # hackonacci(n) modulo 2 has period 7.
    # h[n] = h[n-1] + h[n-3] (mod 2)
    h = [0] * 8
    h[1] = 1  # 1 is odd
    h[2] = 0  # 2 is even
    h[3] = 1  # 3 is odd

    for i in range(4, 8):
        h[i] = (h[i - 1] + h[i - 3]) & 1

    # parity[residue] = hackonacci value mod 2 for n % 7 == residue
    parity = [0] * 7
    for r in range(1, 7):
        parity[r] = h[r]
    parity[0] = h[7]

    # value[r][c] is 1 for Y / odd, 0 for X / even
    # where row index % 7 == r and column index % 7 == c.
    value = [[0] * 7 for _ in range(7)]
    for r in range(7):
        for c in range(7):
            x = (r * c) % 7
            idx = (x * x) % 7
            value[r][c] = parity[idx]

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
            weight = freq[r] * freq[c]
            if weight == 0:
                continue

            current = value[r][c]

            # Clockwise 90 degrees:
            # new(i, j) = old(n + 1 - j, i)
            src_r = (base - c) % 7
            src_c = r
            if current != value[src_r][src_c]:
                diff_90 += weight

            # 180 degrees:
            # new(i, j) = old(n + 1 - i, n + 1 - j)
            src_r = (base - r) % 7
            src_c = (base - c) % 7
            if current != value[src_r][src_c]:
                diff_180 += weight

            # Clockwise 270 degrees:
            # new(i, j) = old(j, n + 1 - i)
            src_r = c
            src_c = (base - r) % 7
            if current != value[src_r][src_c]:
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


if __name__ == "__main__":
    solve()