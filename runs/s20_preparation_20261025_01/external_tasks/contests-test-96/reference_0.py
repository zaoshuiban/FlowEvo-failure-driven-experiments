import functools

MOD_NUM = 998244353

COMB = [[0]*510 for _ in range(510)]
for n in range(510):
    for k in range(1+n):
        if n==k or k==0:
            COMB[n][k] = 1
            continue

        COMB[n][k] = COMB[n-1][k] + COMB[n-1][k-1]
        COMB[n][k] %= MOD_NUM

def comb(n,k):
    return COMB[n][k]


@functools.lru_cache(None)
def dp(n,x):
    if x<=n-1:
        if n>1:
            return pow(x,n,MOD_NUM)
        else:
            return 0

    ans = pow(n-1,n,MOD_NUM)

    for k in range(2,n+1):
        ans += comb(n,k) * pow(n-1,n-k,MOD_NUM) * dp(k, x-n+1)
        ans %= MOD_NUM

    return ans

n,x = map(int,input().split())
print(dp(n,x))
