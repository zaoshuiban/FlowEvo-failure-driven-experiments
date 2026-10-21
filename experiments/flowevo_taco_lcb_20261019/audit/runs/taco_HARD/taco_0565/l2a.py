import sys


def main():
    data = sys.stdin.read().split()
    if len(data) < 3:
        return

    s1, s2, virus = data[0], data[1], data[2]

    n, m, K = len(s1), len(s2), len(virus)

    # Prefix function for the virus
    pi = [0] * K
    for i in range(1, K):
        j = pi[i - 1]
        while j > 0 and virus[i] != virus[j]:
            j = pi[j - 1]
        if virus[i] == virus[j]:
            j += 1
        pi[i] = j

    # KMP automaton transition table.
    # -1 means appending this character would create an occurrence of virus.
    trans = [[-1] * 26 for _ in range(K)]
    for state in range(K):
        for cidx in range(26):
            c = chr(ord('A') + cidx)
            j = state
            while j > 0 and virus[j] != c:
                j = pi[j - 1]
            if virus[j] == c:
                j += 1
            if j == K:
                trans[state][cidx] = -1
            else:
                trans[state][cidx] = j

    a1 = [ord(c) - ord('A') for c in s1]
    a2 = [ord(c) - ord('A') for c in s2]

    W = m + 1
    dp = bytearray((n + 1) * W * K)

    for i in range(n, -1, -1):
        for j in range(m, -1, -1):
            base = (i * W + j) * K

            if i == n and j == m:
                continue

            if i == n:
                nxt = (i * W + (j + 1)) * K
                for k in range(K):
                    dp[base + k] = dp[nxt + k]
            elif j == m:
                nxt = ((i + 1) * W + j) * K
                for k in range(K):
                    dp[base + k] = dp[nxt + k]
            else:
                skip_i = ((i + 1) * W + j) * K
                skip_j = (i * W + (j + 1)) * K

                if a1[i] == a2[j]:
                    cidx = a1[i]
                    diag = ((i + 1) * W + (j + 1)) * K

                    for k in range(K):
                        best = dp[skip_i + k]
                        v = dp[skip_j + k]
                        if v > best:
                            best = v

                        nk = trans[k][cidx]
                        if nk != -1:
                            v = dp[diag + nk] + 1
                            if v > best:
                                best = v

                        dp[base + k] = best
                else:
                    for k in range(K):
                        best = dp[skip_i + k]
                        v = dp[skip_j + k]
                        if v > best:
                            best = v
                        dp[base + k] = best

    i = j = k = 0
    answer = []

    while i < n and j < m:
        base = (i * W + j) * K
        best = dp[base + k]

        if a1[i] == a2[j]:
            nk = trans[k][a1[i]]
            if nk != -1:
                diag = ((i + 1) * W + (j + 1)) * K
                if dp[diag + nk] + 1 == best:
                    answer.append(chr(a1[i] + ord('A')))
                    i += 1
                    j += 1
                    k = nk
                    continue

        if dp[((i + 1) * W + j) * K + k] == best:
            i += 1
        elif dp[(i * W + (j + 1)) * K + k] == best:
            j += 1
        else:
            break

    if answer:
        print(''.join(answer))
    else:
        print(0)


if __name__ == "__main__":
    main()