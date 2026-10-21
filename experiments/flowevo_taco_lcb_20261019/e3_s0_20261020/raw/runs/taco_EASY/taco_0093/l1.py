import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        s = next(it)
        a = [next(it) for _ in range(n)]

        total = sum(a)

        if total < s:
            answers.append("-1")
            continue

        left = 0
        current_sum = 0
        max_length = -1

        for right in range(n):
            current_sum += a[right]

            while current_sum > s and left <= right:
                current_sum -= a[left]
                left += 1

            if current_sum == s:
                max_length = max(max_length, right - left + 1)

        if max_length == -1:
            answers.append("-1")
        else:
            answers.append(str(n - max_length))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()