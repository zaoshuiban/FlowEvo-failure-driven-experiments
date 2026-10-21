import sys


def min_greater(L: bytes, caps):
    """
    Returns the lexicographically smallest string A such that:
        A > L
        count of each character in A <= caps
    If no such string exists, returns None.
    """
    rem = caps.copy()
    n = len(L)

    p = 0
    while p < n:
        idx = L[p] - 97
        if rem[idx] > 0:
            rem[idx] -= 1
            p += 1
        else:
            break

    if p == n:
        # We can match the whole L. The best is to append the smallest
        # available character, if any.
        for d in range(26):
            if rem[d] > 0:
                return L + bytes((97 + d,))

        # No character is left after matching L. Increase a character inside L.
        for i in range(n - 1, -1, -1):
            idx = L[i] - 97
            rem[idx] += 1  # free L[i]

            for d in range(idx + 1, 26):
                if rem[d] > 0:
                    return L[:i] + bytes((97 + d,))

        return None

    # We cannot match L[p]. Try to put a larger character at position p.
    idx = L[p] - 97
    for d in range(idx + 1, 26):
        if rem[d] > 0:
            return L[:p] + bytes((97 + d,))

    # Otherwise, try increasing an earlier position.
    for i in range(p - 1, -1, -1):
        idx = L[i] - 97
        rem[idx] += 1  # free L[i]

        for d in range(idx + 1, 26):
            if rem[d] > 0:
                return L[:i] + bytes((97 + d,))

    return None


def main():
    tokens = sys.stdin.buffer.read().split()
    idx = 0

    N = int(tokens[idx])
    idx += 1

    S = tokens[idx]
    idx += 1

    C = list(map(int, tokens[idx:idx + 26]))
    idx += 26

    K = int(tokens[idx])
    idx += 1

    fixed_less = 0
    suffixes = []

    for _ in range(K):
        P = tokens[idx]
        idx += 1

        m = min(len(P), N)

        diff = -1
        for i in range(m):
            if P[i] != S[i]:
                diff = i
                break

        if diff != -1:
            if P[diff] < S[diff]:
                fixed_less += 1
            # If P[diff] > S[diff], this P can never become smaller than S + A.
        else:
            if len(P) < N:
                # P is a proper prefix of S, so P < S + A always.
                fixed_less += 1
            elif len(P) == N:
                # P == S. It becomes less only when at least one character is appended.
                suffixes.append(b"")
            else:
                # P = S + R. Condition P < S + A is exactly R < A.
                suffixes.append(P[N:])

    suffixes.sort()
    M = len(suffixes)

    possible = bytearray(M + 1)
    possible[0] = 1  # A = empty string

    for q in range(1, M + 1):
        L = suffixes[q - 1]
        U = suffixes[q] if q < M else None

        A = min_greater(L, C)

        if A is not None and (U is None or A <= U):
            possible[q] = 1

    ans = []
    for X in range(K + 1):
        q = X - fixed_less
        if 0 <= q <= M and possible[q]:
            ans.append("Yes")
        else:
            ans.append("No")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    main()