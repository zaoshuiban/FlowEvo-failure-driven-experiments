import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    out = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        bacteria = [1]
        total = 1

        while total < n:
            nxt = min(2 * bacteria[-1], n - total)
            bacteria.append(nxt)
            total += nxt

        bacteria.sort()
        splits = [bacteria[i + 1] - bacteria[i] for i in range(len(bacteria) - 1)]

        out.append(str(len(splits)))
        out.append(" ".join(map(str, splits)))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()