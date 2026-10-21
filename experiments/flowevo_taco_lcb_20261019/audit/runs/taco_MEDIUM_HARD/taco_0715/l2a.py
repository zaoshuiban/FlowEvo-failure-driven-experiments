import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)

        a = [next(it) for _ in range(n)]

        pairs = n // 2
        max_sum = 2 * k

        diff = [0] * (max_sum + 3)
        freq = [0] * (max_sum + 2)

        base_cost = 2 * pairs

        for i in range(pairs):
            u = a[i]
            v = a[n - 1 - i]

            s = u + v
            low = min(u, v) + 1
            high = max(u, v) + k

            diff[low] -= 1
            diff[high + 1] += 1

            freq[s] += 1

        current = 0
        best = 10**9

        for x in range(2, max_sum + 1):
            current += diff[x]
            cost = base_cost + current - freq[x]
            if cost < best:
                best = cost

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()