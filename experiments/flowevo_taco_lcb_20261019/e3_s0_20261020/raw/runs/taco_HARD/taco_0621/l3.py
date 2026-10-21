import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        # For the given constraints every n >= 2 is possible.
        # We build the sequence of bacteria counts after each night.
        counts = [1]
        current_sum = 1

        while current_sum < n:
            nxt = min(2 * counts[-1], n - current_sum)
            counts.append(nxt)
            current_sum += nxt

        counts.sort()

        splits = [
            counts[i + 1] - counts[i]
            for i in range(len(counts) - 1)
        ]

        output.append(str(len(splits)))
        output.append(" ".join(map(str, splits)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()