class Solution:
    def countSteppingNumbers(self, low: str, high: str) -> int:
        MOD = 10**9 + 7
        max_len = max(len(low), len(high))

        # ways[rem][d] = number of ways to append rem digits
        # when the previous digit is d.
        ways = [[0] * 10 for _ in range(max_len + 1)]
        for d in range(10):
            ways[0][d] = 1

        for rem in range(1, max_len + 1):
            for d in range(10):
                total = 0
                if d > 0:
                    total += ways[rem - 1][d - 1]
                if d < 9:
                    total += ways[rem - 1][d + 1]
                ways[rem][d] = total % MOD

        def count_leq(s: str) -> int:
            if s == "0":
                return 0

            n = len(s)
            ans = 0

            # Count all valid stepping numbers with fewer digits.
            for length in range(1, n):
                for first in range(1, 10):
                    ans += ways[length - 1][first]
                ans %= MOD

            # Count valid stepping numbers with the same length and <= s.
            prev = -1
            valid = True

            for i, ch in enumerate(s):
                digit = ord(ch) - ord('0')
                start = 1 if i == 0 else 0

                for d in range(start, digit):
                    if i == 0 or abs(d - prev) == 1:
                        ans += ways[n - i - 1][d]
                        ans %= MOD

                if i == 0:
                    if digit < 1:
                        valid = False
                        break
                    prev = digit
                else:
                    if abs(digit - prev) != 1:
                        valid = False
                        break
                    prev = digit

            if valid:
                ans = (ans + 1) % MOD

            return ans

        def decrement(s: str) -> str:
            arr = list(s)
            i = len(arr) - 1

            while i >= 0 and arr[i] == '0':
                arr[i] = '9'
                i -= 1

            arr[i] = chr(ord(arr[i]) - 1)

            result = ''.join(arr).lstrip('0')
            return result if result else "0"

        return (count_leq(high) - count_leq(decrement(low))) % MOD