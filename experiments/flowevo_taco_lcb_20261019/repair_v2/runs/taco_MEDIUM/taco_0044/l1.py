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

        d = data[idx:idx + n]
        idx += n

        d.sort()

        pairwise_sum = 0
        prefix_sum = 0

        for i, x in enumerate(d):
            pairwise_sum += x * i - prefix_sum
            prefix_sum += x

        answers.append(str(d[-1] - pairwise_sum))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()