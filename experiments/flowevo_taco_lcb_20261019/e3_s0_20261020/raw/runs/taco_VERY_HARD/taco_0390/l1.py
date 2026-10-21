import sys


def main() -> None:
    s = sys.stdin.buffer.readline().strip()
    n = len(s)

    INF = 10**9
    dp = [INF] * (n + 1)
    dp[0] = 0

    # Prefix-function values for the current suffix starting at l.
    pi = [0] * n

    for l in range(n):
        base = dp[l]

        # Substring s[l:l+1], encoded as "1" + character.
        nv = base + 2
        if nv < dp[l + 1]:
            dp[l + 1] = nv

        m = n - l

        for idx in range(1, m):
            length = idx + 1

            q = pi[idx - 1]
            ch = s[l + idx]

            while q > 0 and ch != s[l + q]:
                q = pi[q - 1]

            if ch == s[l + q]:
                q += 1

            pi[idx] = q
            period = length - q

            if length % period == 0:
                count = length // period

                if count < 10:
                    digits = 1
                elif count < 100:
                    digits = 2
                elif count < 1000:
                    digits = 3
                else:
                    digits = 4

                cost = period + digits
            else:
                cost = length + 1

            nv = base + cost
            end = l + length

            if nv < dp[end]:
                dp[end] = nv

    sys.stdout.write(str(dp[n]))


if __name__ == "__main__":
    main()