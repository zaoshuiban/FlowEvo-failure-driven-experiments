import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        n = data[pos]
        k = data[pos + 1]
        pos += 2

        a = data[pos:pos + n]
        pos += n

        pairs = n // 2
        limit = 2 * k

        diff = [0] * (limit + 3)
        exact = [0] * (limit + 3)

        for i in range(pairs):
            left = a[i]
            right = a[n - 1 - i]

            low = min(left, right)
            high = max(left, right)

            diff[low + 1] += 1
            diff[high + k + 1] -= 1

            exact[left + right] += 1

        current = 0
        best_saved = 0

        for target_sum in range(2, limit + 1):
            current += diff[target_sum]
            saved = current + exact[target_sum]
            if saved > best_saved:
                best_saved = saved

        answers.append(str(n - best_saved))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()