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

        left = 0
        right = n - 1

        sum_left = 0
        sum_right = 0
        count_left = 0
        count_right = 0

        answer = 0

        while left <= right:
            if sum_left < sum_right:
                sum_left += w[left]
                left += 1
                count_left += 1
            elif sum_left > sum_right:
                sum_right += w[right]
                right -= 1
                count_right += 1
            else:
                answer = max(answer, count_left + count_right)

                sum_left += w[left]
                left += 1
                count_left += 1

            if sum_left == sum_right:
                answer = max(answer, count_left + count_right)

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()