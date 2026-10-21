import sys

MOD = 998244353

def main():
    S = sys.stdin.readline().strip()
    n = len(S)

    if n % 2 == 1:
        print(0)
        return

    dp = [0] * (n + 2)
    dp[0] = 1

    for ch in S:
        ndp = [0] * (n + 2)

        if ch == '(':
            for balance in range(n):
                if dp[balance]:
                    ndp[balance + 1] = (ndp[balance + 1] + dp[balance]) % MOD
        elif ch == ')':
            for balance in range(1, n + 1):
                if dp[balance]:
                    ndp[balance - 1] = (ndp[balance - 1] + dp[balance]) % MOD
        else:  # ch == '?'
            for balance in range(n + 1):
                if dp[balance]:
                    ndp[balance + 1] = (ndp[balance + 1] + dp[balance]) % MOD
                    if balance > 0:
                        ndp[balance - 1] = (ndp[balance - 1] + dp[balance]) % MOD

        dp = ndp

    print(dp[0] % MOD)

if __name__ == "__main__":
    main()