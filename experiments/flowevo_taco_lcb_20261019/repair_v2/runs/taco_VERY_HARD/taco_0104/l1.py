import sys
import bisect

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]
    b = data[1 + n:1 + 2 * n]

    a.sort()
    b.sort()

    prefix = [0] * (n + 1)
    for i, x in enumerate(b):
        prefix[i + 1] = prefix[i] + x

    total = 0
    for x in a:
        k = bisect.bisect_right(b, x)

        left = x * k - prefix[k]
        right = (prefix[n] - prefix[k]) - x * (n - k)

        total += left + right

    best_matching = 0
    for x, y in zip(a, b):
        best_matching += abs(x - y)

    answer = total - (n - 1) * best_matching
    print(answer)


if __name__ == "__main__":
    solve()