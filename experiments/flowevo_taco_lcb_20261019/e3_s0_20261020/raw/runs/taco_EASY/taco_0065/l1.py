import sys
from bisect import bisect_left
from array import array


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    q = data[0]

    max_r = 0
    for i in range(q):
        r = data[3 * i + 2]
        if r > max_r:
            max_r = r

    n_max = max_r

    f = array('I', [0]) * (n_max + 1)
    f[0] = 1

    g = bytearray(n_max + 1)
    positions = [array('I') for _ in range(10)]

    for n in range(1, n_max + 1):
        digit = n % 10
        prev = n // 10

        if digit == 0:
            fn = f[prev]
        else:
            fn = f[prev] * digit

        f[n] = fn

        if n < 10:
            gn = n
        else:
            gn = g[fn]

        g[n] = gn
        positions[gn].append(n)

    out = []
    idx = 1

    for _ in range(q):
        l = data[idx]
        r = data[idx + 1]
        k = data[idx + 2]
        idx += 3

        arr = positions[k]
        ans = bisect_left(arr, r + 1) - bisect_left(arr, l)
        out.append(str(ans))

    sys.stdout.write('\n'.join(out))


if __name__ == "__main__":
    main()