import sys

MOD = 1_000_000_007

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    outputs = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        typ = [0] * (m + 1)
        left = [0] * (m + 1)
        right = [0] * (m + 1)

        for i in range(1, m + 1):
            typ[i] = next(it)
            left[i] = next(it)
            right[i] = next(it)

        bit = [0] * (m + 2)

        def bit_add(idx, val):
            while idx <= m:
                bit[idx] = (bit[idx] + val) % MOD
                idx += idx & -idx

        def bit_query(idx):
            res = 0
            while idx > 0:
                res = (res + bit[idx]) % MOD
                idx -= idx & -idx
            return res

        diff = [0] * (n + 2)

        for i in range(m, 0, -1):
            executions = (1 + bit_query(i)) % MOD

            if typ[i] == 1:
                l = left[i]
                r = right[i]
                diff[l] = (diff[l] + executions) % MOD
                diff[r + 1] = (diff[r + 1] - executions) % MOD
            else:
                l = left[i]
                r = right[i]

                bit_add(l, executions)
                if r + 1 <= m:
                    bit_add(r + 1, (-executions) % MOD)

        ans = []
        current = 0

        for i in range(1, n + 1):
            current = (current + diff[i]) % MOD
            ans.append(str(current))

        outputs.append(" ".join(ans))

    sys.stdout.write("\n".join(outputs))


if __name__ == "__main__":
    solve()