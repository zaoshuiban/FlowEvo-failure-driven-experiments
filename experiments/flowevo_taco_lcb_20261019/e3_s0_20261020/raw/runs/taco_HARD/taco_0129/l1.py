import sys

MOD = 998244353

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    deg = [0] * (n + 1)
    idx = 1
    for _ in range(n - 1):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        deg[u] += 1
        deg[v] += 1

    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i % MOD

    ans = n
    for i in range(1, n + 1):
        ans = ans * fact[deg[i]] % MOD

    print(ans)

if __name__ == "__main__":
    main()