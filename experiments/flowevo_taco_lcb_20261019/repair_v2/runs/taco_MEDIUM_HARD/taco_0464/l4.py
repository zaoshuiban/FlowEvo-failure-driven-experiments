import sys
import math

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        a = data[idx]
        b = data[idx + 1]
        q = data[idx + 2]
        idx += 3

        period = a // math.gcd(a, b) * b

        pref = [0] * (period + 1)
        good = 0

        for x in range(period):
            if ((x % a) % b) != ((x % b) % a):
                good += 1
            pref[x + 1] = good

        def count_leq(n):
            if n < 0:
                return 0
            cycles, rem = divmod(n + 1, period)
            return cycles * pref[period] + pref[rem]

        answers = []

        for _ in range(q):
            l = data[idx]
            r = data[idx + 1]
            idx += 2

            ans = count_leq(r) - count_leq(l - 1)
            answers.append(str(ans))

        output.append(" ".join(answers))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()