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

    out = ["YES"]
    for x in a:
        colors = [str((j % k) + 1) for j in range(x)]
        out.append(" ".join(colors))

    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    solve()