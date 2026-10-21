class Solution:
    def largestPalindrome(self, n: int, k: int) -> str:
        half_len = (n + 1) // 2
        paired = n // 2

        pow10 = [0] * n
        pow10[0] = 1 % k
        for i in range(1, n):
            pow10[i] = (pow10[i - 1] * 10) % k

        weights = [0] * half_len
        for i in range(half_len):
            if i < paired:
                weights[i] = (pow10[i] + pow10[n - 1 - i]) % k
            else:
                weights[i] = pow10[i] % k

        dp = [0] * (half_len + 1)
        dp[half_len] = 1  # Bit 0 is set: remainder 0 is possible.

        for pos in range(half_len - 1, -1, -1):
            nxt = dp[pos + 1]
            w = weights[pos]
            mask = 0

            possible_rems = []
            for r in range(k):
                if (nxt >> r) & 1:
                    possible_rems.append(r)

            start_digit = 1 if pos == 0 else 0

            for digit in range(start_digit, 10):
                add = (digit * w) % k
                for r in possible_rems:
                    mask |= 1 << ((add + r) % k)

            dp[pos] = mask

        result = []
        current = 0

        for pos in range(half_len):
            w = weights[pos]
            nxt = dp[pos + 1]

            digits = range(9, 0, -1) if pos == 0 else range(9, -1, -1)

            for digit in digits:
                new_rem = (current + digit * w) % k
                required = (-new_rem) % k

                if (nxt >> required) & 1:
                    result.append(str(digit))
                    current = new_rem
                    break

        half = "".join(result)

        if n % 2 == 0:
            return half + half[::-1]
        else:
            return half + half[:-1][::-1]