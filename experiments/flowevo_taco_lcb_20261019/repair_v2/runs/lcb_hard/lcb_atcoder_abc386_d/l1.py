import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    N = int(data[0])
    M = int(data[1])

    bounds = {}
    idx = 2

    for _ in range(M):
        x = int(data[idx])
        y = int(data[idx + 1])
        c = data[idx + 2]
        idx += 3

        if x in bounds:
            low, high = bounds[x]
        else:
            low, high = 0, N

        if c == b'B':
            if y > low:
                low = y
        else:
            upper = y - 1
            if upper < high:
                high = upper

        bounds[x] = (low, high)

    ok = True
    suffix_max_low = 0

    for x in sorted(bounds.keys(), reverse=True):
        low, high = bounds[x]

        if low > suffix_max_low:
            suffix_max_low = low

        if high < suffix_max_low:
            ok = False
            break

    print("Yes" if ok else "No")


if __name__ == "__main__":
    solve()