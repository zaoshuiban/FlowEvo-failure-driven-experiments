import sys

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

        w = data[idx:idx + n]
        idx += n

        # suffix_sum[j] = total weight of the last j candies
        suffix_sum = {0: 0}
        current = 0
        for j in range(1, n + 1):
            current += w[n - j]
            suffix_sum[current] = j

        answer = 0
        prefix = 0

        for i in range(1, n + 1):
            prefix += w[i - 1]

            j = suffix_sum.get(prefix)
            if j is not None and i + j <= n:
                answer = max(answer, i + j)

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()