import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        d = data[idx:idx + n]
        idx += n

        d.sort()

        pair_sum = 0
        prefix_sum = 0

        for i, x in enumerate(d):
            pair_sum += x * i - prefix_sum
            prefix_sum += x

        ans = d[-1] - pair_sum
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()