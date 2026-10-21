import sys


def solve():
    data = sys.stdin.read().strip().split()
    if not data:
        return

    it = iter(data)
    r = int(next(it))
    n = int(next(it))

    # bit 0 -> column 1, bit 1 -> column 2
    available = [3] * r

    for _ in range(n):
        row = int(next(it)) - 1
        col = int(next(it)) - 1

        # The already reclaimed cell cannot be used again.
        available[row] &= ~(1 << col)

        # Opposite-column cells within distance 1 become unavailable.
        opp = 1 - col
        for dr in (-1, 0, 1):
            nr = row + dr
            if 0 <= nr < r:
                available[nr] &= ~(1 << opp)

    memo = {}

    def grundy(l, rr, ml, mr):
        if l > rr:
            return 0

        key = (l, rr, ml, mr)
        if key in memo:
            return memo[key]

        reachable = set()

        for i in range(l, rr + 1):
            if l == rr:
                mask = ml & mr
            elif i == l:
                mask = ml
            elif i == rr:
                mask = mr
            else:
                mask = available[i]

            if mask == 0:
                continue

            for c in (0, 1):
                if not (mask & (1 << c)):
                    continue

                top = 0
                if i > l:
                    a = l
                    b = i - 1

                    left = ml

                    if b == l:
                        mb = ml
                    elif b == rr:
                        mb = mr
                    else:
                        mb = available[b]

                    right = mb & ~(1 << (1 - c))
                    top = grundy(a, b, left, right)

                bottom = 0
                if i < rr:
                    a = i + 1
                    b = rr

                    if a == l:
                        ma = ml
                    elif a == rr:
                        ma = mr
                    else:
                        ma = available[a]

                    left = ma & ~(1 << (1 - c))
                    right = mr
                    bottom = grundy(a, b, left, right)

                reachable.add(top ^ bottom)

        mex = 0
        while mex in reachable:
            mex += 1

        memo[key] = mex
        return mex

    result = grundy(0, r - 1, available[0], available[-1]) if r > 0 else 0
    print("WIN" if result != 0 else "LOSE")


if __name__ == "__main__":
    solve()