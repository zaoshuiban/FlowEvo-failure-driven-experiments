import sys

MOD = 1_000_000_007

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0

    T = data[idx]
    idx += 1

    outputs = []

    for _ in range(T):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        commands = [None] * (m + 1)

        for i in range(1, m + 1):
            t = data[idx]
            l = data[idx + 1]
            r = data[idx + 2]
            idx += 3
            commands[i] = (t, l, r)

        # Fenwick tree for adding to counts of command executions
        bit = [0] * (m + 2)

        # Difference array for final array A
        diff = [0] * (n + 2)

        for i in range(m, 0, -1):
            # Query total extra executions of command i
            s = 0
            j = i
            while j > 0:
                s += bit[j]
                j -= j & -j

            extra = s % MOD
            ways = extra + 1
            if ways >= MOD:
                ways -= MOD

            t, l, r = commands[i]

            if t == 1:
                diff[l] += ways
                if diff[l] >= MOD:
                    diff[l] -= MOD

                if r + 1 <= n:
                    diff[r + 1] -= ways
                    if diff[r + 1] < 0:
                        diff[r + 1] += MOD

            else:
                # Every execution of command i executes commands l..r
                # Add ways to the execution count of commands in [l, r].

                j = l
                while j <= m:
                    bit[j] += ways
                    if bit[j] >= MOD:
                        bit[j] -= MOD
                    j += j & -j

                neg = 0 if ways == 0 else MOD - ways
                j = r + 1
                while j <= m:
                    bit[j] += neg
                    if bit[j] >= MOD:
                        bit[j] -= MOD
                    j += j & -j

        ans = []
        cur = 0

        for i in range(1, n + 1):
            cur += diff[i]
            cur %= MOD
            ans.append(str(cur))

        outputs.append(" ".join(ans))

    sys.stdout.write("\n".join(outputs))


if __name__ == "__main__":
    solve()