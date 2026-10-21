import sys

MOD = 998244353
G = 3
G_INV = 332748118


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
    root = G_INV if invert else G

    while length <= n:
        wlen = pow(root, (mod - 1) // length, mod)
        half = length >> 1

        for start in range(0, n, length):
            w = 1
            end = start + half
            for p in range(start, end):
                u = a[p]
                v = a[p + half] * w % mod

                s = u + v
                if s >= mod:
                    s -= mod

                t = u - v
                if t < 0:
                    t += mod

                a[p] = s
                a[p + half] = t
                w = w * wlen % mod

        length <<= 1

    if invert:
        inv_n = pow(n, mod - 2, mod)
        for i in range(n):
            a[i] = a[i] * inv_n % mod


def solve_case(n, arr):
    mn = min(arr)
    mx = max(arr)
    rng = mx - mn

    # n distinct integers need at least n residues modulo d,
    # so any valid d must be >= n.
    if n > rng:
        return n

    # Check d = n directly first.
    seen = bytearray(n)
    valid_n = True
    for x in arr:
        rem = x % n
        if seen[rem]:
            valid_n = False
            break
        seen[rem] = 1

    if valid_n:
        return n

    start_d = n + 1
    if start_d > rng:
        return start_d

    shifted = [x - mn for x in arr]

    pair_ops = n * (n - 1) // 2

    size = 1
    while size <= 2 * rng:
        size <<= 1

    use_pair = (
        pair_ops <= 100000
        or (pair_ops <= size * size.bit_length() and pair_ops <= 5_000_000)
    )

    diff = bytearray(rng + 1)

    if use_pair:
        shifted.sort()
        for i in range(n):
            ai = shifted[i]
            for j in range(i):
                diff[ai - shifted[j]] = 1
    else:
        a = [0] * size
        for x in shifted:
            a[x] = 1

        ntt(a, False)

        a0 = a[0]
        a[0] = a0 * a0 % MOD

        half_plus = (size + 1) // 2
        for k in range(1, half_plus):
            val = a[k] * a[size - k] % MOD
            a[k] = val
            a[size - k] = val

        if size % 2 == 0:
            mid = size // 2
            a[mid] = a[mid] * a[mid] % MOD

        ntt(a, True)

        for d in range(1, rng + 1):
            if a[d]:
                diff[d] = 1

    d = start_d
    upper = rng + 1

    while d <= upper:
        if d > rng:
            return d

        bad = False
        for multiple in range(d, rng + 1, d):
            if diff[multiple]:
                bad = True
                break

        if not bad:
            return d

        d += 1

    return upper


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        arr = [next(it) for _ in range(n)]
        answers.append(str(solve_case(n, arr)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()