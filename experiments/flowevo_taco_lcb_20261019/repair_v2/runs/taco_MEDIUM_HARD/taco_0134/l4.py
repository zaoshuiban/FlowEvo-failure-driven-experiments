import sys
from bisect import bisect_left, bisect_right


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

        A = data[idx:idx + n]
        idx += n

        B = data[idx:idx + n]
        idx += n

        B.sort()

        count_1 = bisect_right(B, 1)
        count_3 = bisect_right(B, 3) - bisect_left(B, 3)
        count_ge_5 = n - bisect_left(B, 5)

        good_pairs = 0

        for a in A:
            if a == 1:
                continue
            elif a == 2 or a == 4:
                good_pairs += count_1 + count_ge_5
            elif a == 3:
                good_pairs += n - count_3
            else:
                # a >= 5: good b are b == 1 or b > a
                good_pairs += count_1 + (n - bisect_right(B, a))

        answers.append(f"{good_pairs / n:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()