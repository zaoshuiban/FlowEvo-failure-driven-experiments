import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    mn = min(a)
    mx = max(a)

    if mx - mn > k:
        sys.stdout.write("NO\n")
        return

    result = ["YES"]
    base = mn

    for value in a:
        extra = value - base
        colors = []

        # Use color 1 as the base color.
        count_color_one = base + (1 if extra >= 1 else 0)
        colors.extend([1] * count_color_one)

        # Use colors 2, 3, ... for the remaining extra pebbles.
        for color in range(2, extra + 1):
            colors.append(color)

        result.append(" ".join(map(str, colors)))

    sys.stdout.write("\n".join(result))


if __name__ == "__main__":
    solve()