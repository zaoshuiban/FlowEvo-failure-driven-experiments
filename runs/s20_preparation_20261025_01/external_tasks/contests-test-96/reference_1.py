N = 5000
mod = 998244353
fac = [1]*(N+1)
finv = [1]*(N+1)
for i in range(N):
    fac[i+1] = fac[i] * (i+1) % mod
finv[-1] = pow(fac[-1], mod-2, mod)
for i in reversed(range(N)):
    finv[i] = finv[i+1] * (i+1) % mod

def cmb1(n, r, mod):
    if r <0 or r > n:
        return 0
    r = min(r, n-r)
    return fac[n] * finv[r] * finv[n-r] % mod

n, x = map(int, input().split())

dp = [[0]*(x+1) for i in range(n+1)]
dp[n][0] = 1
for i in reversed(range(1, n+1)):
    for j in range(x+1):
        if not dp[i][j]:
            continue
        nj = min(x, i+j-1)
        for k in reversed(range(i+1)):
            dp[k][nj] += cmb1(i, i-k, mod)*pow(nj-j, i-k, mod)*dp[i][j]
            dp[k][nj] %= mod
ans = 0
for i in range(x+1):
    ans += dp[0][i]
    ans %= mod
print(ans)
