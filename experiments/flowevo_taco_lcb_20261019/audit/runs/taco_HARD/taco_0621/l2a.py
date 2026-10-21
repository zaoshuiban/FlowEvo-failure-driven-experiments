import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        total = n - 1

        # Minimum number of nights d such that total can be formed
        d = 0
        max_sum = 0
        while max_sum < total:
            d += 1
            max_sum = (1 << (d + 1)) - 2

        rem = total
        prev = 1
        splits = []

        for i in range(1, d + 1):
            positions_left = d - i + 1
            max_factor = (1 << positions_left) - 1

            low = (rem + max_factor - 1) // max_factor
            high = rem // positions_left

            cur = min(2 * prev, high)

            if cur < prev:
                cur = prev
            if cur < low:
                cur = low

            splits.append(cur - prev)
            rem -= cur
            prev = cur

        output.append(str(d))
        output.append(" ".join(map(str, splits)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()