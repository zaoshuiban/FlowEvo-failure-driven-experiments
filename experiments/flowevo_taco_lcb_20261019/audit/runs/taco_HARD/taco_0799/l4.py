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


def find_root_of_order(p: int, n: int) -> int:
    # n is a power of two and divides p - 1.
    # Find a primitive n-th root modulo p.
    half = n >> 1
    exp = (p - 1) // n
    a = 2

    while True:
        root = pow(a, exp, p)
        if root != 1 and pow(root, half, p) != 1:
            return root
        a += 1


def build_roots(p: int, n: int, root: int):
    roots = [0] * n
    length = 2

    while length <= n:
        half = length >> 1
        wlen = pow(root, n // length, p)
        w = 1

        for j in range(half):
            roots[half + j] = w
            w = w * wlen % p

        length <<= 1

    return roots


def ntt(a, p, roots, rev):
    n = len(a)

    a[:] = [a[i] for i in rev]

    length = 2
    mod = p
    rt = roots

    while length <= n:
        half = length >> 1

        for start in range(0, n, length):
            end = start + half
            j = 0

            for idx in range(start, end):
                u = a[idx]
                v = a[idx + half] * rt[half + j] % mod

                s = u + v
                if s >= mod:
                    s -= mod

                d = u - v
                if d < 0:
                    d += mod

                a[idx] = s
                a[idx + half] = d
                j += 1

        length <<= 1


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    x = data[1]
    a = data[2:2 + n]

    ones_pos = []
    ans0 = 0
    run = 0

    for idx, value in enumerate(a, start=1):
        if value < x:
            ones_pos.append(idx)
            ans0 += run * (run + 1) // 2
            run = 0
        else:
            run += 1

    ans0 += run * (run + 1) // 2

    m = len(ones_pos)
    ans = [0] * (n + 1)
    ans[0] = ans0

    if m == 0:
        sys.stdout.write(" ".join(map(str, ans)))
        return

    left = [0] * m
    prev = 0

    for i, pos in enumerate(ones_pos):
        left[i] = pos - prev
        prev = pos

    right = [0] * m
    nxt = n + 1

    for i in range(m - 1, -1, -1):
        right[i] = nxt - ones_pos[i]
        nxt = ones_pos[i]

    # For small m, direct computation is faster.
    if m <= 700:
        for k in range(1, m + 1):
            total = 0
            limit = m - k
            for i in range(limit + 1):
                total += left[i] * right[i + k - 1]
            ans[k] = total

        sys.stdout.write(" ".join(map(str, ans)))
        return

    need = 2 * m - 1
    size = 1
    while size < need:
        size <<= 1

    limit = n * (n + 1) // 2
    p = ((limit // size) + 1) * size + 1

    while not is_prime(p):
        p += size

    root = find_root_of_order(p, size)
    roots = build_roots(p, size, root)

    rev = [0] * size
    bits = size.bit_length() - 1

    for i in range(1, size):
        rev[i] = (rev[i >> 1] >> 1) | ((i & 1) << (bits - 1))

    fa = left + [0] * (size - m)
    fb = right[::-1] + [0] * (size - m)

    ntt(fa, p, roots, rev)
    ntt(fb, p, roots, rev)

    for i in range(size):
        fa[i] = fa[i] * fb[i] % p

    # Inverse NTT using the reverse trick.
    fa[1:] = fa[:0:-1]
    ntt(fa, p, roots, rev)

    inv_size = pow(size, p - 2, p)
    for i in range(size):
        fa[i] = fa[i] * inv_size % p

    for k in range(1, m + 1):
        ans[k] = fa[m - k]

    sys.stdout.write(" ".join(map(str, ans)))


if __name__ == "__main__":
    main()