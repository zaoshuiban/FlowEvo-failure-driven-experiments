import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    cases = []
    max_x = max_y = 0

    for _ in range(t):
        m, n, p, q = data[idx:idx + 4]
        idx += 4

        x = m - p
        y = n - q
        cases.append((x, y))

        if x > max_x:
            max_x = x
        if y > max_y:
            max_y = y

    # Precompute all losing positions (P-positions) up to max_x, max_y.
    losing = set()

    # col_losing[j] is True if there is a losing position in column j
    # with a smaller first coordinate.
    col_losing = bytearray(max_y + 1)

    # diag_losing[d] is True if there is a losing position on diagonal
    # first - second = d with a smaller first coordinate.
    offset = max_y
    diag_losing = bytearray(max_x + max_y + 3)

    for i in range(max_x + 1):
        row_has_losing = False

        for j in range(max_y + 1):
            d = i - j + offset

            if row_has_losing or col_losing[j] or diag_losing[d]:
                continue

            # No move can reach a previous losing position, so this is losing.
            losing.add((i, j))
            row_has_losing = True
            col_losing[j] = 1
            diag_losing[d] = 1

    ans = []
    for x, y in cases:
        if (x, y) in losing:
            ans.append("Bob")
        else:
            ans.append("Alice")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()