import sys


def xor_upto(n: int) -> int:
    if n < 0:
        return 0
    m = n & 3
    if m == 0:
        return n
    if m == 1:
        return 1
    if m == 2:
        return n + 1
    return 0


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    out = []
    BITS = range(16, -1, -1)

    for _ in range(t):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        n = r - l + 1

        if n & 1:
            xa = 0
            end = idx + n
            while idx < end:
                xa ^= data[idx]
                idx += 1

            ans = xa ^ xor_upto(r) ^ xor_upto(l - 1)
            out.append(str(ans))
            continue

        a = [0] * n
        ch0 = [-1]
        ch1 = [-1]

        for i in range(n):
            v = data[idx]
            idx += 1
            a[i] = v

            node = 0
            for b in BITS:
                if (v >> b) & 1:
                    nxt = ch1[node]
                    if nxt == -1:
                        nxt = len(ch0)
                        ch1[node] = nxt
                        ch0.append(-1)
                        ch1.append(-1)
                    node = nxt
                else:
                    nxt = ch0[node]
                    if nxt == -1:
                        nxt = len(ch0)
                        ch0[node] = nxt
                        ch0.append(-1)
                        ch1.append(-1)
                    node = nxt

        ans = 0

        for v in a:
            x = v ^ l

            node = 0
            mn = 0

            for b in BITS:
                xb = (x >> b) & 1
                if xb == 0:
                    nxt = ch0[node]
                    if nxt != -1:
                        node = nxt
                    else:
                        node = ch1[node]
                        mn |= 1 << b
                else:
                    nxt = ch1[node]
                    if nxt != -1:
                        node = nxt
                    else:
                        node = ch0[node]
                        mn |= 1 << b

            if mn != l:
                continue

            node = 0
            mx = 0

            for b in BITS:
                xb = (x >> b) & 1
                if xb == 0:
                    nxt = ch1[node]
                    if nxt != -1:
                        node = nxt
                        mx |= 1 << b
                    else:
                        node = ch0[node]
                else:
                    nxt = ch0[node]
                    if nxt != -1:
                        node = nxt
                        mx |= 1 << b
                    else:
                        node = ch1[node]

            if mx == r:
                ans = x
                break

        out.append(str(ans))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()