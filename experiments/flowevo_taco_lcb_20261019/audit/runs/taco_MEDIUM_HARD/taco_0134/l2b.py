import sys
from bisect import bisect_left, bisect_right

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        A = [next(it) for _ in range(n)]
        B = [next(it) for _ in range(n)]

        B.sort()

        count1 = bisect_right(B, 1)  # all B are positive, so this counts 1s
        count3 = bisect_right(B, 3) - bisect_left(B, 3)

        first_ge_5 = bisect_left(B, 5)
        count_ge_5 = n - first_ge_5

        total = 0

        for a in A:
            if a == 1:
                continue
            elif a == 3:
                total += n - count3
            elif a == 2 or a == 4:
                total += count1 + count_ge_5
            else:  # a >= 5
                total += count1 + (n - bisect_right(B, a))

        answers.append(f"{total / n:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()