import sys

MOD = 1_000_000_007
MAXN = 100

# Fibonacci string lengths: L[1] = L[2] = 1, L[i] = L[i-1] + L[i-2]
fib_len = [0] * (MAXN + 1)
fib_len[1] = 1
fib_len[2] = 1
for i in range(3, MAXN + 1):
    fib_len[i] = fib_len[i - 1] + fib_len[i - 2]


def build_fib(n: int) -> bytes:
    if n == 1:
        return b"a"
    if n == 2:
        return b"b"

    prev2 = b"a"  # F1
    prev1 = b"b"  # F2

    for _ in range(3, n + 1):
        cur = prev1 + prev2
        prev2 = prev1
        prev1 = cur

    return prev1


def prefix_function(p: bytes):
    n = len(p)
    pi = [0] * n

    for i in range(1, n):
        j = pi[i - 1]
        while j > 0 and p[i] != p[j]:
            j = pi[j - 1]
        if p[i] == p[j]:
            j += 1
        pi[i] = j

    return pi


def kmp_count(text: bytes, p: bytes, pi) -> int:
    n = len(p)
    j = 0
    cnt = 0

    for ch in text:
        while j > 0 and ch != p[j]:
            j = pi[j - 1]
        if ch == p[j]:
            j += 1

        if j == n:
            cnt += 1
            j = pi[j - 1]

    return cnt % MOD


def count_on_prefixes(text: bytes, p: bytes, pi, indices, lengths):
    n = len(p)
    j = 0
    cnt = 0
    ptr = 0
    result = {}

    for pos, ch in enumerate(text, 1):
        while j > 0 and ch != p[j]:
            j = pi[j - 1]
        if ch == p[j]:
            j += 1

        if j == n:
            cnt += 1
            j = pi[j - 1]

        while ptr < len(lengths) and pos == lengths[ptr]:
            result[indices[ptr]] = cnt % MOD
            ptr += 1

    return result


def apply_power(a, b, xA, xB, q, rem):
    # One 2-step block:
    # a' = a + b + xA
    # b' = a + 2b + xA + xB
    #
    # Affine transform:
    # (a, b) -> (A*a + B*b + C, D*a + E*b + F)

    A, B, C = 1, 0, 0
    D, E, F = 0, 1, 0

    bA, bB, bC = 1, 1, xA % MOD
    bD, bE, bF = 1, 2, (xA + xB) % MOD

    while q:
        if q & 1:
            nA = (bA * A + bB * D) % MOD
            nB = (bA * B + bB * E) % MOD
            nC = (bA * C + bB * F + bC) % MOD

            nD = (bD * A + bE * D) % MOD
            nE = (bD * B + bE * E) % MOD
            nF = (bD * C + bE * F + bF) % MOD

            A, B, C, D, E, F = nA, nB, nC, nD, nE, nF

        nA = (bA * bA + bB * bD) % MOD
        nB = (bA * bB + bB * bE) % MOD
        nC = (bA * bC + bB * bF + bC) % MOD

        nD = (bD * bA + bE * bD) % MOD
        nE = (bD * bB + bE * bE) % MOD
        nF = (bD * bC + bE * bF + bF) % MOD

        bA, bB, bC, bD, bE, bF = nA, nB, nC, nD, nE, nF
        q >>= 1

    na = (A * a + B * b + C) % MOD
    nb = (D * a + E * b + F) % MOD

    if rem:
        return (na + nb + xA) % MOD
    return nb


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    k = int(data[0])
    m = int(data[1])
    patterns = data[2:2 + m]

    answers = []

    for p in patterns:
        L = len(p)

        # Minimal r such that |F_r| >= L
        r = 1
        while fib_len[r] < L:
            r += 1

        # F_k is too short
        if k < r:
            answers.append("0")
            continue

        B = r + 5

        # For small k, just build the Fibonacci string directly.
        if k <= B + 2:
            text = build_fib(int(k))
            pi = prefix_function(p)
            answers.append(str(kmp_count(text, p, pi)))
            continue

        # Build F_{B+2}. It contains F_{B-1}, F_B, F_{B+1}, F_{B+2}
        # as prefixes.
        n = B + 2
        text = build_fib(n)
        pi = prefix_function(p)

        indices = [B - 1, B, B + 1, B + 2]
        lengths = [fib_len[i] for i in indices]

        counts = count_on_prefixes(text, p, pi, indices, lengths)

        c_prev = counts[B - 1]
        c_cur = counts[B]
        c_next = counts[B + 1]
        c_next2 = counts[B + 2]

        # X_n is the number of occurrences crossing the boundary in
        # F_n = F_{n-1} F_{n-2}. For large n it is 2-periodic.
        xA = (c_next - c_cur - c_prev) % MOD       # X_{B+1}
        xB = (c_next2 - c_next - c_cur) % MOD      # X_{B+2}

        # Current state is (C_{B+1}, C_{B+2})
        a = c_next
        b = c_next2

        steps = k - (B + 2)
        q = steps // 2
        rem = steps & 1

        ans = apply_power(a, b, xA, xB, q, rem)
        answers.append(str(ans % MOD))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()