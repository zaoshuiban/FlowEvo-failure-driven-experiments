import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        weights = [next(it) for _ in range(n)]

        suffix_sum_to_count = {0: 0}
        current_sum = 0

        for count in range(1, n + 1):
            current_sum += weights[n - count]
            suffix_sum_to_count[current_sum] = count

        prefix_sum = 0
        answer = 0

        for left_count in range(n + 1):
            if left_count > 0:
                prefix_sum += weights[left_count - 1]

            right_count = suffix_sum_to_count.get(prefix_sum)

            if right_count is not None and left_count + right_count <= n:
                answer = max(answer, left_count + right_count)

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()