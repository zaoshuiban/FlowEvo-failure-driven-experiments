import sys

MOD = 998244353


def solve() -> None:
    S = sys.stdin.buffer.readline().strip()
    n = len(S)

    U = bytearray(n)
    L = bytearray(n)

    for i, ch in enumerate(S):
        if ch == 63:  # '?'
            U[i] = 26
            L[i] = 26
        elif 65 <= ch <= 90:  # uppercase
            U[i] = 1
            L[i] = 0
        else:  # lowercase
            U[i] = 0
            L[i] = 1

    # C[i] = number of ways for S[i:] to have the form U* L*
    C = [0] * (n + 1)
    C[n] = 1
    suffix_l = 1
    c_next = 1

    for i in range(n - 1, -1, -1):
        li = L[i]
        ui = U[i]
        ci = (ui * c_next + li * suffix_l) % MOD
        C[i] = ci
        suffix_l = (li * suffix_l) % MOD
        c_next = ci

    pow26 = [1] * (n + 1)
    for i in range(1, n + 1):
        pow26[i] = pow26[i - 1] * 26 % MOD

    invnum = [0] * 27
    for i in range(1, 27):
        invnum[i] = pow(i, MOD - 2, MOD)

    inv26 = invnum[26]

    ans = C[0]

    # Prefix information before current position
    q = 0          # number of '?' in prefix
    fixed = 0      # number of distinct fixed uppercase letters in prefix
    mask = 0
    duplicated = False

    for i in range(n):
        li = L[i]

        if li and i + 1 < n and not duplicated:
            u_next = U[i + 1]
            if u_next:
                suffix_after = u_next * C[i + 2] % MOD

                if suffix_after:
                    avail = 26 - fixed
                    max_k = q if q < avail else avail

                    term = pow26[q]
                    a = term

                    for k in range(1, max_k + 1):
                        term = term * (q - k + 1) % MOD
                        term = term * (avail - k + 1) % MOD
                        term = term * invnum[k] % MOD
                        term = term * inv26 % MOD

                        a += term
                        if a >= MOD:
                            a -= MOD

                    ans = (ans + a * li % MOD * suffix_after) % MOD

        ui = U[i]

        if ui == 26:  # '?'
            q += 1
        elif ui == 1:  # fixed uppercase
            bit = 1 << (S[i] - 65)
            if mask & bit:
                duplicated = True
            else:
                mask |= bit
                fixed += 1

    print(ans % MOD)


if __name__ == "__main__":
    solve()