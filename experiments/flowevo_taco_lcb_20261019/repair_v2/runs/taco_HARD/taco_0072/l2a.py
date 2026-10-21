import sys

FULL = 3


def advance_free(S, g):
    """Advance through g consecutive completely free columns."""
    if g <= 0 or S == 0:
        return S

    p0 = S & 1   # state 0 is possible
    p1 = S & 2   # state 1 is possible
    p2 = S & 4   # state 2 is possible
    p3 = S & 8   # state 3 is possible

    if g == 1:
        res = 0
        if p0 or p3:
            res |= 1 << 0
        if p2:
            res |= 1 << 1
        if p1:
            res |= 1 << 2
        if p0:
            res |= 1 << 3
        return res

    both03 = bool(p0 or p3)
    res = 0

    if both03:
        res |= (1 << 0) | (1 << 3)

    if g & 1:
        # Odd g >= 3
        if p2:
            res |= 1 << 1
        if p1:
            res |= 1 << 2
    else:
        # Even g >= 2
        if p1:
            res |= 1 << 1
        if p2:
            res |= 1 << 2

    return res


def advance_block(S, blocked):
    """Advance through one column with blocked cells mask."""
    res = 0

    for prev in range(4):
        if (S & (1 << prev)) == 0:
            continue
        if prev & blocked:
            continue

        remaining = FULL ^ (blocked | prev)

        if remaining == 0:
            res |= 1 << 0
        elif remaining == 1:
            res |= 1 << 1
        elif remaining == 2:
            res |= 1 << 2
        else:  # remaining == 3
            res |= (1 << 0) | (1 << 3)

    return res


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        blocks = []

        for _ in range(m):
            r = data[idx]
            c = data[idx + 1]
            idx += 2
            blocks.append((c, 1 << (r - 1)))

        blocks.sort()

        # Bit i means frontier mask i is reachable.
        S = 1  # initially frontier mask 0
        prev_col = 0

        i = 0
        while i < m:
            c = blocks[i][0]
            blocked = 0

            while i < m and blocks[i][0] == c:
                blocked |= blocks[i][1]
                i += 1

            gap = c - prev_col - 1
            if gap > 0:
                S = advance_free(S, gap)

            S = advance_block(S, blocked)
            prev_col = c

        S = advance_free(S, n - prev_col)

        answers.append("YES" if (S & 1) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()