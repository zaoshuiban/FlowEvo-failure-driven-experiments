import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        d = [next(it) for _ in range(n)]
        d.sort()

        max_d = d[-1]

        # Sum of |d[i] - d[j]| over all i < j
        pairwise_sum = 0
        for i, value in enumerate(d):
            pairwise_sum += value * (2 * i - n + 1)

        answers.append(str(max_d - pairwise_sum))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()