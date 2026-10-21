import sys

MOD = 998244353
PRIMITIVE_ROOT = 3


def ntt(a, invert):
    n = len(a)

    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]

    length = 2
    mod = MOD
    root = PRIMITIVE_ROOT

    while length <= n:
        wlen = pow(root, (mod - 1) // length, mod)
        if invert:
            wlen = pow(wlen, mod - 2, mod)

        half = length >> 1

        for start in range(0, n, length):
            w = 1
            end = start + half
            for idx in range(start, end):
                u = a[idx]
                v = a[idx + half] * w % mod

                s = u + v
                if s >= mod:
                    s -= mod

                d = u - v
                if d < 0:
                    d += mod

                a[idx] = s
                a[idx + half] = d
                w = w * wlen % mod

        length <<= 1

    if invert:
        inv_n = pow(n, mod - 2, mod)
        for i in range(n):
            a[i] = a[i] * inv_n % mod


def solve_case(arr):
    n = len(arr)
    m = max(arr)

    # d < n is impossible by pigeonhole principle.
    # Check d = n first, because it is often the answer.
    seen = set()
    valid = True
    for x in arr:
        r = x % n
        if r in seen:
            valid = False
            break
        seen.add(r)

    if valid:
        return n

    # For small n, direct pairwise differences are faster.
    if n * (n - 1) // 2 <= 200000:
        arr.sort()
        diff = bytearray(m + 1)

        for i in range(n):
            ai = arr[i]
            for j in range(i):
                diff[ai - arr[j]] = 1

        for d in range(n, m + 1):
            ok = True
            for delta in range(d, m + 1, d):
                if diff[delta]:
                    ok = False
                    break
            if ok:
                return d

        return m

    # Use NTT to compute all pairwise differences.
    size = 1
    while size <= 2 * m:
        size <<= 1

    f = [0] * size
    for x in arr:
        f[x] = 1

    ntt(f, False)

    w = pow(PRIMITIVE_ROOT, (MOD - 1) // size, MOD)
    base = pow(w, m, MOD)

    h = [0] * size
    cur = 1

    for k in range(size):
        idx = 0 if k == 0 else size - k
        h[k] = f[k] * f[idx] % MOD * cur % MOD
        cur = cur * base % MOD

    ntt(h, True)

    for d in range(n, m + 1):
        ok = True
        for delta in range(d, m + 1, d):
            if h[m + delta] != 0:
                ok = False
                break
        if ok:
            return d

    return m


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        n = data[pos]
        pos += 1
        arr = data[pos:pos + n]
        pos += n

        answers.append(str(solve_case(arr)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()