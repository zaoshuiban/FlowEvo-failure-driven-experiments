import sys


def is_prime(n: int) -> bool:
    if n < 2:
        return False

    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small_primes:
        if n % p == 0:
            return n == p

    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    # Deterministic Miller-Rabin bases for 64-bit integers
    for a in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False

    return True


def ntt(a, invert, mod, rev, roots, n):
    for i in range(n):
        j = rev[i]
        if i < j:
            a[i], a[j] = a[j], a[i]

    length = 2
    while length <= n:
        half = length >> 1
        step = n // length

        for start in range(0, n, length):
            j = start
            end = start + half

            if not invert:
                wpos = 0
                while j < end:
                    u = a[j]
                    v = a[j + half] * roots[wpos] % mod

                    s = u + v
                    if s >= mod:
                        s -= mod

                    d = u - v
                    if d < 0:
                        d += mod

                    a[j] = s
                    a[j + half] = d

                    wpos += step
                    j += 1
            else:
                wpos = 0
                while j < end:
                    u = a[j]
                    v = a[j + half] * roots[wpos] % mod

                    s = u + v
                    if s >= mod:
                        s -= mod

                    d = u - v
                    if d < 0:
                        d += mod

                    a[j] = s
                    a[j + half] = d

                    wpos -= step
                    if wpos < 0:
                        wpos += n
                    j += 1

        length <<= 1

    if invert:
        inv_n = pow(n, mod - 2, mod)
        for i in range(n):
            a[i] = a[i] * inv_n % mod


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    x = data[1]
    arr = data[2:2 + n]

    m = sum(1 for v in arr if v < x)

    freq = [0] * (m + 1)
    freq[0] = 1

    pref = 0
    for v in arr:
        if v < x:
            pref += 1
        freq[pref] += 1

    ans = [0] * (n + 1)

    # For small number of elements < x, direct computation is faster.
    if m <= 1000:
        c0 = 0
        for v in range(m + 1):
            c0 += freq[v] * freq[v]

        ans[0] = (c0 - (n + 1)) // 2

        for k in range(1, m + 1):
            total = 0
            limit = m - k + 1
            for v in range(limit):
                total += freq[v] * freq[v + k]
            ans[k] = total

        print(*ans)
        return

    conv_len = 2 * m + 1
    size = 1 << ((conv_len - 1).bit_length())

    # Find an NTT-friendly prime larger than any possible coefficient.
    bound = (n + 1) * (n + 1)
    k = bound // size + 1

    while True:
        mod = k * size + 1
        if is_prime(mod):
            break
        k += 1

    # Find a primitive size-th root of unity modulo mod.
    exp = (mod - 1) // size
    cand = 2
    while True:
        root = pow(cand, exp, mod)
        if pow(root, size // 2, mod) != 1:
            break
        cand += 1

    rev = [0] * size
    lg = size.bit_length() - 1
    for i in range(1, size):
        rev[i] = (rev[i >> 1] >> 1) | ((i & 1) << (lg - 1))

    roots = [1] * size
    for i in range(1, size):
        roots[i] = roots[i - 1] * root % mod

    a = freq + [0] * (size - len(freq))
    ntt(a, False, mod, rev, roots, size)

    transformed = a[:]
    step_factor = pow(root, len(freq) - 1, mod)
    factor = 1
    mask = size - 1

    for i in range(size):
        a[i] = transformed[i] * transformed[(-i) & mask] % mod * factor % mod
        factor = factor * step_factor % mod

    del transformed

    ntt(a, True, mod, rev, roots, size)

    ans[0] = (a[m] - (n + 1)) // 2

    for k in range(1, m + 1):
        ans[k] = a[m + k]

    print(*ans)


if __name__ == "__main__":
    main()