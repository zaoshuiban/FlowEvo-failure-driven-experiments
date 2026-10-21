import sys
from functools import lru_cache

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    r, n = data[0], data[1]

    # Bit 0 -> column 1, bit 1 -> column 2.
    # Initially every cell is available.
    base = [3] * (r + 2)

    idx = 2
    for _ in range(n):
        row = data[idx]
        col = data[idx + 1] - 1
        idx += 2

        opp = 1 - col

        # The whole row becomes unavailable because the opposite cell in
        # the same row is forbidden by the reclaimed cell.
        base[row] = 0

        # Opposite-column cells in neighbouring rows become forbidden.
        if row > 1:
            base[row - 1] &= ~(1 << opp)
        if row < r:
            base[row + 1] &= ~(1 << opp)

    @lru_cache(None)
    def grundy(l, u, ml, mu):
        if l > u:
            return 0

        if l == u:
            return 1 if (ml & mu) else 0

        reachable = set()

        for i in range(l, u + 1):
            if i == l:
                mask = ml
            elif i == u:
                mask = mu
            else:
                mask = base[i]

            if mask == 0:
                continue

            for c in (0, 1):
                if not (mask & (1 << c)):
                    continue

                removed = 1 << (1 - c)

                # Game above row i after choosing (i, c)
                if i > l:
                    k = i - 1
                    if k == l:
                        cur = ml
                        new_mask = cur & ~removed
                        top = grundy(l, l, new_mask, new_mask)
                    else:
                        cur = base[k]
                        new_mask = cur & ~removed
                        top = grundy(l, k, ml, new_mask)
                else:
                    top = 0

                # Game below row i after choosing (i, c)
                if i < u:
                    k = i + 1
                    if k == u:
                        cur = mu
                        new_mask = cur & ~removed
                        bottom = grundy(u, u, new_mask, new_mask)
                    else:
                        cur = base[k]
                        new_mask = cur & ~removed
                        bottom = grundy(k, u, new_mask, mu)
                else:
                    bottom = 0

                reachable.add(top ^ bottom)

        g = 0
        while g in reachable:
            g += 1
        return g

    answer = grundy(1, r, base[1], base[r])
    print("WIN" if answer != 0 else "LOSE")


if __name__ == "__main__":
    main()