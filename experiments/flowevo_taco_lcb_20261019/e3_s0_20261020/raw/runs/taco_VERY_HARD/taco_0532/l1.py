import sys


def solve():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        t = next(data)
    except StopIteration:
        return

    answers = []

    for _ in range(t):
        n = next(data)
        d = next(data)

        p = [next(data) for _ in range(n)]

        possible = True
        for i, value in enumerate(p):
            if (value - 1) % d != i % d:
                possible = False
                break

        if not possible:
            answers.append("-1")
            continue

        base = [0] * d
        length = [0] * d
        total = 0

        for r in range(d):
            base[r] = total
            m = (n - 1 - r) // d + 1
            length[r] = m
            total += m

        bit = [0] * (total + 1)
        seen = [0] * d

        answer = 0
        r = 0

        for value in p:
            rank = (value - 1) // d + 1

            b = base[r]
            m = length[r]

            count_leq = 0
            j = rank
            while j > 0:
                count_leq += bit[b + j]
                j -= j & -j

            answer += seen[r] - count_leq

            j = rank
            while j <= m:
                bit[b + j] += 1
                j += j & -j

            seen[r] += 1

            r += 1
            if r == d:
                r = 0

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()