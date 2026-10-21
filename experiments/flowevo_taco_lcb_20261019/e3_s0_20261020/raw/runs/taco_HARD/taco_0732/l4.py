import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    rows = next(it)
    n = next(it)

    occupied = {}
    for _ in range(n):
        r = next(it)
        c = next(it) - 1
        occupied[r] = c

    # dp[m][left_mask][right_mask]
    # m consecutive rows, with unavailable cells given by masks
    # at the first and last row.
    dp = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(rows + 1)]

    for m in range(1, rows + 1):
        for left_mask in range(4):
            for right_mask in range(4):
                reachable = set()

                for i in range(1, m + 1):
                    for c in (0, 1):
                        bit = 1 << c

                        if i == 1 and (left_mask & bit):
                            continue
                        if i == m and (right_mask & bit):
                            continue

                        opposite = 1 << (1 - c)
                        value = 0

                        if i > 1:
                            value ^= dp[i - 1][left_mask][opposite]

                        if i < m:
                            value ^= dp[m - i][opposite][right_mask]

                        reachable.add(value)

                mex = 0
                while mex in reachable:
                    mex += 1

                dp[m][left_mask][right_mask] = mex

    xor_sum = 0
    prev_row = 0
    prev_col = None

    for row in sorted(occupied):
        col = occupied[row]

        length = row - prev_row - 1
        if length > 0:
            left_mask = 0
            if prev_col is not None:
                left_mask = 1 << (1 - prev_col)

            right_mask = 1 << (1 - col)
            xor_sum ^= dp[length][left_mask][right_mask]

        prev_row = row
        prev_col = col

    length = rows - prev_row
    if length > 0:
        left_mask = 0
        if prev_col is not None:
            left_mask = 1 << (1 - prev_col)

        xor_sum ^= dp[length][left_mask][0]

    print("WIN" if xor_sum != 0 else "LOSE")


if __name__ == "__main__":
    main()