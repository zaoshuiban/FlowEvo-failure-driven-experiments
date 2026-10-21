import sys

MOD = 998244353

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        pref = 0
        cnt = 1  # number of previous prefix sums, initially P[0] = 0

        s1 = 0   # sum of previous prefix sums
        s2 = 0   # sum of squares of previous prefix sums
        s3 = 0   # sum of cubes of previous prefix sums

        ans = 0

        for _ in range(n):
            pref = (pref + next(it)) % MOD
            p = pref

            p2 = p * p % MOD
            p3 = p2 * p % MOD

            term = (
                cnt * p3
                - 3 * p2 * s1
                + 3 * p * s2
                - s3
            ) % MOD

            ans = (ans + term) % MOD

            s1 = (s1 + p) % MOD
            s2 = (s2 + p2) % MOD
            s3 = (s3 + p3) % MOD
            cnt += 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()