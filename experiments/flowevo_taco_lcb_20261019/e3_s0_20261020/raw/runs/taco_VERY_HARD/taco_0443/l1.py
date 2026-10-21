import sys

MOD = 10**9 + 7

def solve():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))

        values = []
        counts = []

        current = 0
        ans = 0

        for idx in range(1, n + 1):
            a = int(next(it))

            removed_count = 0
            removed_sum = 0

            while values and values[-1] <= a:
                v = values.pop()
                c = counts.pop()

                removed_count += c
                removed_sum += v * c

            current = current - removed_sum + a * (removed_count + 1)

            values.append(a)
            counts.append(removed_count + 1)

            ans = (ans + current * (n - idx + 1)) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()