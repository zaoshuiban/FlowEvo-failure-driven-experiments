import sys

MOD = 998244353


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    k = int(data[1])
    s = data[2]

    bits = [c & 1 for c in s]
    total_ones = sum(bits)

    if k == 0 or k > total_ones:
        print(1)
        return

    # If the whole string consists of ones, shuffling any valid substring
    # cannot change it.
    if total_ones == n:
        print(1)
        return

    fac = [1] * (n + 1)
    for i in range(1, n + 1):
        fac[i] = fac[i - 1] * i % MOD

    invfac = [1] * (n + 1)
    invfac[n] = pow(fac[n], MOD - 2, MOD)
    for i in range(n, 0, -1):
        invfac[i - 1] = invfac[i] * i % MOD

    # If k equals the total number of ones, we can shuffle the whole string.
    if k == total_ones:
        ans = fac[n] * invfac[total_ones] % MOD * invfac[n - total_ones] % MOD
        print(ans)
        return

    ans = 1  # The original string

    f = fac
    inv = invfac
    b = bits
    mod = MOD
    N = n
    K = k

    for left in range(N - 1):
        a = b[left]
        ones_in_interval = a
        subtotal = 0

        for right in range(left + 1, N):
            cbit = b[right]
            ones_in_interval += cbit

            if ones_in_interval > K:
                break

            length_inside = right - left - 1

            # Number of ones that must be placed inside after flipping
            # both endpoint characters.
            need = ones_in_interval - (2 - a - cbit)

            if 0 <= need <= length_inside:
                ways = f[length_inside] * inv[need] % mod
                ways = ways * inv[length_inside - need] % mod
                subtotal += ways

        ans = (ans + subtotal) % mod

    print(ans)


if __name__ == "__main__":
    solve()