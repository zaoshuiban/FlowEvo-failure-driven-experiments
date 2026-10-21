import sys


def solve():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        d = next(it)
        p = [next(it) for _ in range(n)]

        possible = True
        for i, value in enumerate(p):
            if (value - 1 - i) % d != 0:
                possible = False
                break

        if not possible:
            answers.append("-1")
            continue

        inversions = 0

        max_rem = min(d - 1, n - 1)

        for rem in range(max_rem + 1):
            length = (n - 1 - rem) // d + 1

            if length <= 1:
                continue

            bit = [0] * (length + 1)
            seen = 0

            for pos in range(rem, n, d):
                rank = (p[pos] - 1) // d
                idx = rank + 1

                count_leq = 0
                j = idx
                while j > 0:
                    count_leq += bit[j]
                    j -= j & -j

                inversions += seen - count_leq

                j = idx
                while j <= length:
                    bit[j] += 1
                    j += j & -j

                seen += 1

        answers.append(str(inversions))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()