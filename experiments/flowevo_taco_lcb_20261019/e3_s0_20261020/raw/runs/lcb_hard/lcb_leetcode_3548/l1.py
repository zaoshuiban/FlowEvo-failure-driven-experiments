class Solution:
    def countGoodIntegers(self, n: int, k: int) -> int:
        half_len = (n + 1) // 2
        start = 10 ** (half_len - 1)
        end = 10 ** half_len

        seen = set()

        for i in range(start, end):
            left = str(i)
            if n % 2 == 1:
                palindrome = left + left[:-1][::-1]
            else:
                palindrome = left + left[::-1]

            if int(palindrome) % k == 0:
                count = [0] * 10
                for ch in palindrome:
                    count[ord(ch) - ord('0')] += 1
                seen.add(tuple(count))

        fact = [1] * (n + 1)
        for i in range(1, n + 1):
            fact[i] = fact[i - 1] * i

        answer = 0

        for count in seen:
            denominator = 1
            for c in count:
                denominator *= fact[c]

            ways = fact[n] // denominator

            if count[0] > 0:
                bad_denominator = fact[count[0] - 1]
                for digit in range(1, 10):
                    bad_denominator *= fact[count[digit]]
                ways -= fact[n - 1] // bad_denominator

            answer += ways

        return answer