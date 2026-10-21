import sys
from collections import defaultdict


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        x = data[idx]
        idx += 1

        freq = defaultdict(int)
        for a in arr:
            freq[a & x] += 1

        ans = 0
        for count in freq.values():
            ans += count * count

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()