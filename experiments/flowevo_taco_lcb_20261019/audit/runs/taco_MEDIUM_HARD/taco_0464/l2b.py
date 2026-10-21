import sys
import math

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    output = []

    for _ in range(t):
        a = next(it)
        b = next(it)
        q = next(it)

        period = a * b // math.gcd(a, b)

        pref = [0] * (period + 1)
        count_good = 0

        for x in range(period):
            if ((x % a) % b) != ((x % b) % a):
                count_good += 1
            pref[x + 1] = count_good

        def count_up_to(n):
            if n < 0:
                return 0
            full, rem = divmod(n + 1, period)
            return full * count_good + pref[rem]

        answers = []
        for _ in range(q):
            l = next(it)
            r = next(it)
            answers.append(str(count_up_to(r) - count_up_to(l - 1)))

        output.append(" ".join(answers))

    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()