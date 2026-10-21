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

        period = a // math.gcd(a, b) * b

        pref = [0] * period
        cnt = 0

        for x in range(period):
            if ((x % a) % b) == ((x % b) % a):
                cnt += 1
            pref[x] = cnt

        total = pref[-1]

        def count_equal(n):
            if n < 0:
                return 0
            cycles, rem = divmod(n + 1, period)
            result = cycles * total
            if rem:
                result += pref[rem - 1]
            return result

        answers = []

        for _ in range(q):
            l = next(it)
            r = next(it)

            equal_count = count_equal(r) - count_equal(l - 1)
            answers.append(str((r - l + 1) - equal_count))

        output.append(" ".join(answers))

    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()