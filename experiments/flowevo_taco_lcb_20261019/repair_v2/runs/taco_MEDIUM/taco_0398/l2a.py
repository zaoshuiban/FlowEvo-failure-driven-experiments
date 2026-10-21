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

        pair_diff_sum = 0
        for i, value in enumerate(d):
            pair_diff_sum += value * (2 * i - n + 1)

        max_d = d[-1]
        answers.append(str(max_d - pair_diff_sum))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()