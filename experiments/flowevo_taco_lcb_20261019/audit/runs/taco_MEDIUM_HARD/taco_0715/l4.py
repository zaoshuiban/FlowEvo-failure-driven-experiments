import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        pairs = n // 2
        max_sum = 2 * k

        diff = [0] * (max_sum + 3)
        freq = [0] * (max_sum + 3)

        for i in range(pairs):
            left = a[i]
            right = a[n - 1 - i]

            total = left + right
            freq[total] += 1

            low = min(left, right)
            high = max(left, right)

            diff[low + 1] += 1
            diff[high + k + 1] -= 1

        current = 0
        best = n

        for target in range(2, max_sum + 1):
            current += diff[target]
            replacements = n - current - freq[target]
            if replacements < best:
                best = replacements

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()