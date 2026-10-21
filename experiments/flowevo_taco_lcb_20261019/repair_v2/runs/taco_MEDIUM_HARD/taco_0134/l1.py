import sys
from bisect import bisect_left, bisect_right

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    T = data[idx]
    idx += 1

    answers = []

    for _ in range(T):
        N = data[idx]
        idx += 1

        A = data[idx:idx + N]
        idx += N

        B = data[idx:idx + N]
        idx += N

        B.sort()

        count_1 = bisect_right(B, 1) - bisect_left(B, 1)
        count_3 = bisect_right(B, 3) - bisect_left(B, 3)
        count_ge_5 = N - bisect_left(B, 5)

        good_pairs = 0

        for a in A:
            if a == 1:
                continue
            elif a == 3:
                good_pairs += N - count_3
            elif a == 2 or a == 4:
                good_pairs += count_1 + count_ge_5
            else:
                # For a >= 5, a^b > b^a iff b > a, and also b = 1.
                good_pairs += count_1 + (N - bisect_right(B, a))

        expected = good_pairs / N
        answers.append(f"{expected:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()