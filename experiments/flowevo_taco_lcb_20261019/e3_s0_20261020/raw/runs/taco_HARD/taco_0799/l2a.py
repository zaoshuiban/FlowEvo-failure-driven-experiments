import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, x = data[0], data[1]
    arr = data[2:2 + n]

    pos = []
    ans0 = 0
    run = 0

    for i, val in enumerate(arr):
        if val < x:
            pos.append(i)
            ans0 += run * (run + 1) // 2
            run = 0
        else:
            run += 1

    ans0 += run * (run + 1) // 2

    m = len(pos)
    ans = [0] * (n + 1)
    ans[0] = ans0

    if m == 0:
        sys.stdout.write(' '.join(map(str, ans)) + '\n')
        return

    # Gap array d. For a block of k consecutive elements < x,
    # the number of valid segments is sum d[i] * d[i + k].
    d = [0] * (m + 1)
    d[0] = pos[0] + 1

    for i in range(1, m):
        d[i] = pos[i] - pos[i - 1]

    d[m] = n - pos[-1]

    gsize = m + 1
    need = 2 * gsize - 1
    L = 1
    while L < need:
        L <<= 1

    # Large NTT-friendly prime:
    # MOD = 15 * 2^37 + 1
    MOD = 2061584302081

    # Find a primitive root modulo MOD.
    factors = (2, 3, 5)
    primitive = 2
    while True:
        ok = True
        for q in factors:
            if pow(primitive, (MOD - 1) // q, MOD) == 1:
                ok = False
                break
        if ok:
            break
        primitive += 1

    rev = [0] * L
    bits = L.bit_length() - 1
    for i in range(1, L):
        rev[i] = (rev[i >> 1] >> 1) | ((i & 1) << (bits - 1))

    roots_f = []
    roots_i = []

    length = 2
    while length <= L:
        half = length >> 1
        wlen = pow(primitive, (MOD - 1) // length, MOD)
        wlen_inv = pow(wlen, MOD - 2, MOD)

        rf = [1] * half
        ri = [1] * half

        for j in range(1, half):
            rf[j] = rf[j - 1] * wlen % MOD
            ri[j] = ri[j - 1] * wlen_inv % MOD

        roots_f.append(rf)
        roots_i.append(ri)
        length <<= 1

    a = [0] * L
    for i, v in enumerate(d):
        a[i] = v

    def ntt(arr, roots):
        n_local = L
        mod = MOD
        rev_local = rev

        for i in range(n_local):
            j = rev_local[i]
            if i < j:
                arr[i], arr[j] = arr[j], arr[i]

        length = 2
        level = 0

        while length <= n_local:
            half = length >> 1
            rt = roots[level]

            for start in range(0, n_local, length):
                j = start
                k = start + half
                r = 0
                end = k

                while j < end:
                    u = arr[j]
                    v = arr[k] * rt[r] % mod

                    s = u + v
                    if s >= mod:
                        s -= mod

                    t = u - v
                    if t < 0:
                        t += mod

                    arr[j] = s
                    arr[k] = t

                    j += 1
                    k += 1
                    r += 1

            length <<= 1
            level += 1

    ntt(a, roots_f)

    # Circular autocorrelation: F[t] * F[-t].
    mid = L >> 1

    a0 = a[0] * a[0] % MOD
    a[0] = a0

    for i in range(1, mid):
        prod = a[i] * a[L - i] % MOD
        a[i] = prod
        a[L - i] = prod

    amid = a[mid] * a[mid] % MOD
    a[mid] = amid

    ntt(a, roots_i)

    invL = pow(L, MOD - 2, MOD)

    for k in range(1, m + 1):
        ans[k] = a[L - k] * invL % MOD

    sys.stdout.write(' '.join(map(str, ans)) + '\n')


if __name__ == "__main__":
    solve()