import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        scores = data[idx:idx + n]
        idx += n

        freq = [0] * 101
        for score in scores:
            freq[score] += 1

        less_or_equal = 0
        answer = 0

        for score in range(101):
            count = freq[score]
            if count == 0:
                continue

            less_or_equal += count

            if less_or_equal > n - less_or_equal:
                answer += count

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()