import sys

MOD = 10**9 + 7

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    out = []
    pow2 = [1]

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        while len(pow2) < n:
            pow2.append((pow2[-1] * 2) % MOD)

        arr.sort()

        ans = 0
        for i, value in enumerate(arr):
            ways = (pow2[i] - pow2[n - 1 - i]) % MOD
            ans = (ans + (value % MOD) * ways) % MOD

        out.append(str(ans))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()