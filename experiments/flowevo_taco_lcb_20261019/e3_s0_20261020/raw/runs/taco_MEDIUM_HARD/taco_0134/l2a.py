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

        freq1 = B.count(1)
        freq3 = B.count(3)
        B.sort()

        good_pairs = 0

        for a in A:
            if a == 1:
                continue
            elif a == 2 or a == 4:
                good_pairs += freq1 + (n - bisect_left(B, 5))
            elif a == 3:
                good_pairs += n - freq3
            else:  # a >= 5
                good_pairs += freq1 + (n - bisect_right(B, a))

        answers.append(f"{good_pairs / n:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()