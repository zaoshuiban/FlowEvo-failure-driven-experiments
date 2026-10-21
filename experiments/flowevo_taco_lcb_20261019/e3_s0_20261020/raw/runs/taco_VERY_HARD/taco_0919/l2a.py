import sys
import math


def solve():
    data = sys.stdin.buffer.read()
    if not data:
        return

    idx = 0

    def next_int():
        nonlocal idx
        n = len(data)
        while idx < n and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < n and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    T = next_int()
    answers = []

    for _ in range(T):
        N = next_int()
        E = next_int()
        O = next_int()

        total = N * (N + 1) // 2

        if E + O != total:
            answers.append("-1")
            continue

        # If c0 is the number of even prefix sums among N+1 prefixes,
        # then O = c0 * (N + 1 - c0).
        M = N + 1
        D = M * M - 4 * O

        if D < 0:
            answers.append("-1")
            continue

        root = math.isqrt(D)
        if root * root != D:
            answers.append("-1")
            continue

        k = None
        for candidate in ((M - root) // 2, (M + root) // 2):
            if 1 <= candidate <= M and candidate * (M - candidate) == O:
                k = candidate
                break

        if k is None:
            answers.append("-1")
            continue

        # Construct an array with all even values (2), except one odd value (1)
        # at position k, if k <= N.
        if N == 0:
            answers.append("")
        elif k > N:
            answers.append("2 " * (N - 1) + "2")
        else:
            answers.append("2 " * (k - 1) + "1" + " 2" * (N - k))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()