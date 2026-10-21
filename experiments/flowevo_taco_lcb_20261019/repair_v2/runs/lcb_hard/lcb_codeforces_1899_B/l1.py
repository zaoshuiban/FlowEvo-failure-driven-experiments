import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        prefix = [0] * (n + 1)
        for i, x in enumerate(a):
            prefix[i + 1] = prefix[i] + x

        ans = 0

        for k in range(1, n + 1):
            if n % k != 0:
                continue

            min_sum = 10**30
            max_sum = -1

            for start in range(0, n, k):
                group_sum = prefix[start + k] - prefix[start]
                if group_sum < min_sum:
                    min_sum = group_sum
                if group_sum > max_sum:
                    max_sum = group_sum

            diff = max_sum - min_sum
            if diff > ans:
                ans = diff

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()