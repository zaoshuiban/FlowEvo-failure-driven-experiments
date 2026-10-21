import sys

MOD = 1_000_000_007


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    T = data[idx]
    idx += 1

    outputs = []

    for _ in range(T):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        typ = [0] * (m + 1)
        L = [0] * (m + 1)
        R = [0] * (m + 1)

        for i in range(1, m + 1):
            typ[i] = data[idx]
            L[i] = data[idx + 1]
            R[i] = data[idx + 2]
            idx += 3

        bit = [0] * (m + 2)
        diff = [0] * (n + 3)

        for i in range(m, 0, -1):
            # Query number of extra executions of command i
            s = 0
            x = i
            while x > 0:
                s += bit[x]
                if s >= MOD:
                    s -= MOD
                x -= x & -x

            ways = s + 1
            if ways >= MOD:
                ways -= MOD

            if typ[i] == 1:
                l = L[i]
                r = R[i]

                diff[l] += ways
                if diff[l] >= MOD:
                    diff[l] -= MOD

                diff[r + 1] -= ways
                if diff[r + 1] < 0:
                    diff[r + 1] += MOD
            else:
                l = L[i]
                r = R[i]

                x = l
                while x <= m:
                    bit[x] += ways
                    if bit[x] >= MOD:
                        bit[x] -= MOD
                    x += x & -x

                neg = MOD - ways if ways else 0
                x = r + 1
                while x <= m:
                    bit[x] += neg
                    if bit[x] >= MOD:
                        bit[x] -= MOD
                    x += x & -x

        cur = 0
        ans = []

        for i in range(1, n + 1):
            cur += diff[i]
            cur %= MOD
            ans.append(str(cur))

        outputs.append(" ".join(ans))

    sys.stdout.write("\n".join(outputs))


if __name__ == "__main__":
    solve()