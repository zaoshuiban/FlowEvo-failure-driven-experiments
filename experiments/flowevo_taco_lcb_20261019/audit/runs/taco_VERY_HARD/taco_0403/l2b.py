import sys

MOD = 998244353
PRIMITIVE_ROOT = 3


def ntt(a, invert):
    n = len(a)
    mod = MOD

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
    while length <= n:
        wlen = pow(PRIMITIVE_ROOT, (mod - 1) // length, mod)
        if invert:
            wlen = pow(wlen, mod - 2, mod)

        half = length >> 1
        for start in range(0, n, length):
            w = 1
            end = start + half
            pos = start

            while pos < end:
                u = a[pos]
                v = a[pos + half] * w % mod

                x = u + v
                if x >= mod:
                    x -= mod

                y = u - v
                if y < 0:
                    y += mod

                a[pos] = x
                a[pos + half] = y

                w = w * wlen % mod
                pos += 1

        length <<= 1

    if invert:
        inv_n = pow(n, mod - 2, mod)
        for i in range(n):
            a[i] = a[i] * inv_n % mod


def solve_case(a):
    n = len(a)
    mn = min(a)
    mx = max(a)
    max_diff = mx - mn

    if n > max_diff:
        return n

    pairs = n * (n - 1) // 2

    if pairs <= 20000:
        diff = bytearray(max_diff + 1)

        for i in range(n):
            ai = a[i]
            for j in range(i + 1, n):
                d = ai - a[j]
                if d < 0:
                    d = -d
                diff[d] = 1

        for d in range(n, max_diff + 1):
            bad = False
            for multiple in range(d, max_diff + 1, d):
                if diff[multiple]:
                    bad = True
                    break

            if not bad:
                return d

        return max_diff + 1

    length = max_diff + 1
    size = 1
    required = 2 * length - 1

    while size < required:
        size <<= 1

    p = [0] * size
    q = [0] * size

    for value in a:
        pos = value - mn
        p[pos] = 1
        q[max_diff - pos] = 1

    ntt(p, False)
    ntt(q, False)

    for i in range(size):
        p[i] = p[i] * q[i] % MOD

    ntt(p, True)

    for d in range(n, max_diff + 1):
        bad = False

        for multiple in range(d, max_diff + 1, d):
            if p[max_diff + multiple]:
                bad = True
                break

        if not bad:
            return d

    return max_diff + 1


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        answers.append(str(solve_case(a)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()