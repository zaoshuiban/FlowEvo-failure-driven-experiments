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

        d = data[idx:idx + n]
        idx += n

        d.sort()

        prefix_sum = 0
        pair_sum = 0

        for i, value in enumerate(d):
            # Sum of (value - previous_value) over all previous values
            pair_sum += i * value - prefix_sum
            prefix_sum += value

        answer = d[-1] - pair_sum
        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()