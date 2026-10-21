class Solution:
    def countKReducibleNumbers(self, s: str, k: int) -> int:
        MOD = 10**9 + 7
        n = len(s)

        # dp[x] = number of operations needed to reduce x to 1
        # for x <= n. Since n can be represented by at most n set bits.
        dp = [0] * (n + 1)
        for x in range(2, n + 1):
            dp[x] = 1 + dp[x.bit_count()]

        # Precompute binomial coefficients modulo MOD.
        comb = [[0] * (n + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            comb[i][0] = comb[i][i] = 1
            for j in range(1, i):
                comb[i][j] = (comb[i - 1][j - 1] + comb[i - 1][j]) % MOD

        # count[c] = number of positive integers < int(s, 2)
        # whose binary representation has exactly c set bits.
        count = [0] * (n + 1)
        ones = 0

        for i, ch in enumerate(s):
            if ch == '1':
                remaining = n - i - 1

                for extra_ones in range(remaining + 1):
                    c = ones + extra_ones
                    count[c] = (count[c] + comb[remaining][extra_ones]) % MOD

                ones += 1

        answer = 0

        for c in range(1, n + 1):
            if c <= n and dp[c] < k:
                answer = (answer + count[c]) % MOD

        return answer