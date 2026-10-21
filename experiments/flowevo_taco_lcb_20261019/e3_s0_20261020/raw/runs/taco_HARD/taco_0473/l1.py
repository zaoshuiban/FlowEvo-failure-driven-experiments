import sys

MOD = 1_000_000_007
MAXV = 60005

# Precompute modular inverses up to max possible N + K.
inv = [0] * MAXV
inv[1] = 1
for i in range(2, MAXV):
    inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    out = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        m = data[idx + 2]
        idx += 3

        # f0 = probability that a guess among n boxes is wrong
        f0 = (n - 1) * inv[n] % MOD

        if m & 1:
            # M = 2s - 1: s blocks of length 1
            s = (m + 1) // 2
            fail = pow(f0, s, MOD)
        else:
            # M = 2s: one block of length 2 and s - 1 blocks of length 1
            s = m // 2
            f1 = (n + k - 1) * inv[n + k] % MOD
            fail = pow(f0, s, MOD) * f1 % MOD

        ans = (1 - fail) % MOD
        out.append(str(ans))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()