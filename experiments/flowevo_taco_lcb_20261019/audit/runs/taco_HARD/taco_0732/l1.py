import sys
from functools import lru_cache


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    r, n = data[0], data[1]
    selected = [0] * (r + 2)  # 0 = none, otherwise selected column: 1 or 2

    idx = 2
    for _ in range(n):
        row = data[idx]
        col = data[idx + 1]
        idx += 2
        selected[row] = col

    FULL = 3

    def blocked_by(col: int) -> int:
        # Selecting column col forbids the opposite column in adjacent rows.
        opposite = 3 - col
        return 1 << (opposite - 1)

    # Available columns mask for every row after the already reclaimed cells.
    mask = [0] * (r + 2)

    for i in range(1, r + 1):
        if selected[i] != 0:
            mask[i] = 0
        else:
            m = FULL
            if selected[i - 1] != 0:
                m &= ~blocked_by(selected[i - 1])
            if selected[i + 1] != 0:
                m &= ~blocked_by(selected[i + 1])
            mask[i] = m

    @lru_cache(maxsize=None)
    def grundy(left: int, right: int, left_blocked: int, right_blocked: int) -> int:
        if left > right:
            return 0

        reachable = set()

        for row in range(left, right + 1):
            if left == right:
                available = FULL & ~(left_blocked | right_blocked)
            elif row == left:
                available = FULL & ~left_blocked
            elif row == right:
                available = FULL & ~right_blocked
            else:
                available = FULL

            if available == 0:
                continue

            for col in (0, 1):
                if not (available & (1 << col)):
                    continue

                # This move blocks the opposite column in adjacent rows.
                new_block = 1 << (1 - col)

                top_sg = (
                    grundy(left, row - 1, left_blocked, new_block)
                    if left <= row - 1
                    else 0
                )
                bottom_sg = (
                    grundy(row + 1, right, new_block, right_blocked)
                    if row + 1 <= right
                    else 0
                )

                reachable.add(top_sg ^ bottom_sg)

        mex = 0
        while mex in reachable:
            mex += 1
        return mex

    total_sg = 0
    i = 1

    while i <= r:
        if mask[i] == 0:
            i += 1
            continue

        left = i
        while i <= r and mask[i] != 0:
            i += 1
        right = i - 1

        left_blocked = (
            blocked_by(selected[left - 1]) if selected[left - 1] != 0 else 0
        )
        right_blocked = (
            blocked_by(selected[right + 1]) if selected[right + 1] != 0 else 0
        )

        total_sg ^= grundy(left, right, left_blocked, right_blocked)

    print("WIN" if total_sg != 0 else "LOSE")


if __name__ == "__main__":
    main()