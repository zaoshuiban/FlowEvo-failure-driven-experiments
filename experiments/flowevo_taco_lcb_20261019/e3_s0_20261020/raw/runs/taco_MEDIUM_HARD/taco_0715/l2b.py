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
        exact_sum_count = [0] * (max_sum + 3)

        for i in range(pairs):
            left = a[i]
            right = a[n - 1 - i]

            low = min(left, right)
            high = max(left, right)

            l = low + 1
            r = high + k

            diff[l] += 1
            diff[r + 1] -= 1

            exact_sum_count[left + right] += 1

        current = 0
        best = 0

        for x in range(2, max_sum + 1):
            current += diff[x]
            score = current + exact_sum_count[x]
            if score > best:
                best = score

        answers.append(str(n - best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()