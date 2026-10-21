import sys
from collections import defaultdict


def min_greater(L: bytes, C):
    """
    Returns the lexicographically smallest string A such that:
        A > L, and count(A, ch) <= C[ch] for all ch
    Returns None if no such string exists.
    """
    n = len(L)
    cnt = [0] * 26
    for b in L:
        cnt[b - 97] += 1

    fits = True
    for i in range(26):
        if cnt[i] > C[i]:
            fits = False
            break

    # Best case: L itself can be used, then append the smallest available char.
    if fits:
        for c in range(26):
            if cnt[c] < C[c]:
                return L + bytes((97 + c,))

    viol = 0
    for i in range(26):
        if cnt[i] > C[i]:
            viol += 1

    # Find the rightmost possible divergence from L.
    for pos in range(n - 1, -1, -1):
        x = L[pos] - 97

        old_bad = cnt[x] > C[x]
        cnt[x] -= 1
        new_bad = cnt[x] > C[x]

        if old_bad and not new_bad:
            viol -= 1
        elif new_bad and not old_bad:
            viol += 1

        # cnt now stores counts of L[:pos]
        if viol == 0:
            for c in range(x + 1, 26):
                if cnt[c] < C[c]:
                    return L[:pos] + bytes((97 + c,))

    return None


def solve():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    N = int(next(it))
    S = next(it)

    C = [int(next(it)) for _ in range(26)]

    K = int(next(it))

    base = 0
    var_count = defaultdict(int)

    for _ in range(K):
        P = next(it)

        if P.startswith(S):
            R = P[N:]
            var_count[R] += 1
        else:
            if S > P:
                base += 1

    M = sum(var_count.values())

    possible_y = [False] * (M + 1)
    possible_y[0] = True  # A = empty string

    items = sorted(var_count.items())  # sorted by R lexicographically
    d = len(items)

    cumulative = 0

    for idx, (R, freq) in enumerate(items):
        cumulative += freq
        y = cumulative

        A = min_greater(R, C)

        if A is not None:
            if idx == d - 1 or A <= items[idx + 1][0]:
                possible_y[y] = True

    possible_total = [False] * (K + 1)

    for y in range(M + 1):
        if possible_y[y]:
            total = base + y
            if total <= K:
                possible_total[total] = True

    ans = []
    for x in range(K + 1):
        ans.append("Yes" if possible_total[x] else "No")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()