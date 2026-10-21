import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    N = int(data[0])
    S = data[1]

    idx = 2
    C = list(map(int, data[idx:idx + 26]))
    idx += 26

    K = int(data[idx])
    idx += 1
    P_strings = data[idx:idx + K]

    n = len(S)

    fixed = 0
    dynamic_suffixes = []

    for P in P_strings:
        p = len(P)
        m = min(n, p)

        diff = -1
        for j in range(m):
            if P[j] != S[j]:
                diff = j
                break

        if diff != -1:
            if P[diff] < S[diff]:
                fixed += 1
        else:
            if p < n:
                fixed += 1
            elif p == n:
                dynamic_suffixes.append(b"")
            else:
                dynamic_suffixes.append(P[n:])

    M = len(dynamic_suffixes)
    achievable = [False] * (M + 1)
    achievable[0] = True

    if M > 0:
        dynamic_suffixes.sort()

        groups = []
        cur = dynamic_suffixes[0]
        cnt = 1

        for s in dynamic_suffixes[1:]:
            if s == cur:
                cnt += 1
            else:
                groups.append((cur, cnt))
                cur = s
                cnt = 1
        groups.append((cur, cnt))

        def min_greater(v):
            used = [0] * 26
            for ch in v:
                used[ch - 97] += 1

            bad = 0
            for i in range(26):
                if used[i] > C[i]:
                    bad += 1

            # v + one extra character
            if bad == 0:
                for c in range(26):
                    if used[c] < C[c]:
                        return v + bytes([97 + c])

            # Increase some character of v and drop the suffix
            for pos in range(len(v) - 1, -1, -1):
                ci = v[pos] - 97

                old_bad = used[ci] > C[ci]
                used[ci] -= 1
                new_bad = used[ci] > C[ci]

                if old_bad and not new_bad:
                    bad -= 1

                if bad != 0:
                    continue

                for c in range(ci + 1, 26):
                    if used[c] < C[c]:
                        return v[:pos] + bytes([97 + c])

            return None

        cumulative = 0
        group_count = len(groups)

        for i, (v, cnt) in enumerate(groups):
            cumulative += cnt
            g = min_greater(v)

            if g is None:
                continue

            if i + 1 < group_count:
                if g <= groups[i + 1][0]:
                    achievable[cumulative] = True
            else:
                achievable[cumulative] = True

    ans = [False] * (K + 1)

    for f, ok in enumerate(achievable):
        if ok:
            x = fixed + f
            if x <= K:
                ans[x] = True

    sys.stdout.write("\n".join("Yes" if ans[x] else "No" for x in range(K + 1)))


if __name__ == "__main__":
    main()