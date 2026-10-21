import sys


def xor_upto(k):
    if k < 0:
        return 0
    m = k & 3
    if m == 0:
        return k
    if m == 1:
        return 1
    if m == 2:
        return k + 1
    return 0


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    out = []
    bits = [1 << b for b in range(16, -1, -1)]

    for _ in range(t):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        n = r - l + 1
        a = data[idx:idx + n]
        idx += n

        if n & 1:
            xor_a = 0
            for v in a:
                xor_a ^= v

            xor_range = xor_upto(r) ^ xor_upto(l - 1)
            out.append(str(xor_a ^ xor_range))
            continue

        ch0 = [0]
        ch1 = [0]

        for v in a:
            node = 0
            for bit in bits:
                if v & bit:
                    nxt = ch1[node]
                    if nxt == 0:
                        nxt = len(ch0)
                        ch1[node] = nxt
                        ch0.append(0)
                        ch1.append(0)
                    node = nxt
                else:
                    nxt = ch0[node]
                    if nxt == 0:
                        nxt = len(ch0)
                        ch0[node] = nxt
                        ch0.append(0)
                        ch1.append(0)
                    node = nxt

        answer = 0

        for v in a:
            x = v ^ l

            node = 0
            minimum = 0

            for bit in bits:
                if x & bit:
                    if ch1[node]:
                        node = ch1[node]
                    else:
                        node = ch0[node]
                        minimum += bit
                else:
                    if ch0[node]:
                        node = ch0[node]
                    else:
                        node = ch1[node]
                        minimum += bit

            if minimum != l:
                continue

            node = 0
            maximum = 0

            for bit in bits:
                if x & bit:
                    if ch0[node]:
                        node = ch0[node]
                        maximum += bit
                    else:
                        node = ch1[node]
                else:
                    if ch1[node]:
                        node = ch1[node]
                        maximum += bit
                    else:
                        node = ch0[node]

            if maximum == r:
                answer = x
                break

        out.append(str(answer))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()