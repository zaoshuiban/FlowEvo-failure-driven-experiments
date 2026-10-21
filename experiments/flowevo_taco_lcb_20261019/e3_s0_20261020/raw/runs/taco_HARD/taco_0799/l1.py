import sys


def is_prime(num: int) -> bool:
    if num < 2:
        return False

    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small_primes:
        if num % p == 0:
            return num == p

    d = num - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    for a in (2, 3, 5, 7, 11, 13, 17):
        if a >= num:
            continue
        x = pow(a, d, num)
        if x == 1 or x == num - 1:
            continue

        for _ in range(s - 1):
            x = x * x % num
            if x == num - 1:
                break
        else:
            return False

    return True


def find_prime(target: int, maxn: int) -> int:
    p = (target // maxn) * maxn + 1
    while p < target or not is_prime(p):
        p += maxn
    return p


def prepare_roots(n: int, root: int, mod: int):
    inv_root = pow(root, mod - 2, mod)

    forward_roots = []
    length = n
    while length > 1:
        half = length >> 1
        wlen = pow(root, n // length, mod)

        ws = [1] * half
        cur = 1
        for j in range(1, half):
            cur = cur * wlen % mod
            ws[j] = cur

        forward_roots.append(ws)
        length >>= 1

    inverse_roots = []
    length = 2
    while length <= n:
        half = length >> 1
        wlen = pow(inv_root, n // length, mod)

        ws = [1] * half
        cur = 1
        for j in range(1, half):
            cur = cur * wlen % mod
            ws[j] = cur

        inverse_roots.append(ws)
        length <<= 1

    return forward_roots, inverse_roots


def ntt_forward(a, roots, mod, n):
    length = n
    level = 0

    while length > 1:
        half = length >> 1
        ws = roots[level]

        for start in range(0, n, length):
            idx = start
            u = a[idx]
            v = a[idx + half]

            s = u + v
            if s >= mod:
                s -= mod

            d = u - v
            if d < 0:
                d += mod

            a[idx] = s
            a[idx + half] = d

            for j in range(1, half):
                idx = start + j
                u = a[idx]
                v = a[idx + half]

                s = u + v
                if s >= mod:
                    s -= mod

                d = u - v
                if d < 0:
                    d += mod

                a[idx] = s
                a[idx + half] = d * ws[j] % mod

        length = half
        level += 1


def ntt_inverse(a, roots, mod, n):
    length = 2
    level = 0

    while length <= n:
        half = length >> 1
        ws = roots[level]

        for start in range(0, n, length):
            idx = start
            u = a[idx]
            v = a[idx + half]

            s = u + v
            if s >= mod:
                s -= mod

            d = u - v
            if d < 0:
                d += mod

            a[idx] = s
            a[idx + half] = d

            for j in range(1, half):
                idx = start + j
                u = a[idx]
                v = a[idx + half] * ws[j] % mod

                s = u + v
                if s >= mod:
                    s -= mod

                d = u - v
                if d < 0:
                    d += mod

                a[idx] = s
                a[idx + half] = d

        length <<= 1
        level += 1

    inv_n = pow(n, mod - 2, mod)
    for i in range(n):
        a[i] = a[i] * inv_n % mod


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    x = data[1]
    arr = data[2:2 + n]

    less_positions = []
    for i, value in enumerate(arr, 1):
        if value < x:
            less_positions.append(i)

    m = len(less_positions)
    answer = [0] * (n + 1)

    if m == 0:
        answer[0] = n * (n + 1) // 2
        sys.stdout.write(" ".join(map(str, answer)) + "\n")
        return

    gaps = [0] * (m + 1)

    gaps[0] = less_positions[0]
    for i in range(1, m):
        gaps[i] = less_positions[i] - less_positions[i - 1]
    gaps[m] = n + 1 - less_positions[-1]

    zero_count = 0
    for v in gaps:
        z = v - 1
        zero_count += z * (z + 1) // 2

    answer[0] = zero_count

    size = m + 1
    convolution_len = 2 * size - 1

    ntt_size = 1
    while ntt_size < convolution_len:
        ntt_size <<= 1

    max_root_power = 1 << 19
    upper_bound = (n + 1) * (n + 1) + 1
    mod = find_prime(upper_bound, max_root_power)

    primitive = None
    a = 2
    while True:
        r = pow(a, (mod - 1) // max_root_power, mod)
        if pow(r, max_root_power // 2, mod) != 1:
            primitive = r
            break
        a += 1

    root = pow(primitive, max_root_power // ntt_size, mod)

    forward_roots, inverse_roots = prepare_roots(ntt_size, root, mod)

    fa = gaps + [0] * (ntt_size - size)
    fb = gaps[::-1] + [0] * (ntt_size - size)

    ntt_forward(fa, forward_roots, mod, ntt_size)
    ntt_forward(fb, forward_roots, mod, ntt_size)

    for i in range(ntt_size):
        fa[i] = fa[i] * fb[i] % mod

    ntt_inverse(fa, inverse_roots, mod, ntt_size)

    offset = size - 1

    for k in range(1, m + 1):
        answer[k] = fa[offset + k]

    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    solve()