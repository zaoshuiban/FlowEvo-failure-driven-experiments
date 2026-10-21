import sys
import math

data = list(map(int, sys.stdin.buffer.read().split()))
idx = 0

t = data[idx]
idx += 1

output = []

for _ in range(t):
    a = data[idx]
    b = data[idx + 1]
    q = data[idx + 2]
    idx += 3

    period = a // math.gcd(a, b) * b

    pref = [0] * (period + 1)
    count = 0

    for x in range(1, period + 1):
        if ((x % a) % b) != ((x % b) % a):
            count += 1
        pref[x] = count

    def count_valid(n):
        if n <= 0:
            return 0
        return (n // period) * count + pref[n % period]

    answers = []

    for _ in range(q):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        answer = count_valid(r) - count_valid(l - 1)
        answers.append(str(answer))

    output.append(" ".join(answers))

sys.stdout.write("\n".join(output))