import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    if max(a) - min(a) > k:
        sys.stdout.write("NO\n")
        return

    base = min(a)
    out = ["YES"]

    for x in a:
        extra = x - base
        # base pebbles of color 1, then one extra pebble of colors 1..extra
        colors = [1] * base + list(range(1, extra + 1))
        out.append(" ".join(map(str, colors)))

    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    solve()