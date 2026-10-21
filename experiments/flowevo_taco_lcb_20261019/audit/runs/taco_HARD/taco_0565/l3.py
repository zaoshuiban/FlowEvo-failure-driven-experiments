import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if len(data) < 3:
        return

    s1, s2, virus = data[0], data[1], data[2]
    n1, n2, m = len(s1), len(s2), len(virus)

    # KMP prefix function for virus
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and virus[i] != virus[j]:
            j = pi[j - 1]
        if virus[i] == virus[j]:
            j += 1
        pi[i] = j

    # KMP automaton:
    # trans[state][c] = next state, or -1 if appending c creates virus
    trans = [[-1] * 26 for _ in range(m)]
    for state in range(m):
        for c in range(26):
            ch = ord('A') + c
            q = state
            while q > 0 and virus[q] != ch:
                q = pi[q - 1]
            if virus[q] == ch:
                q += 1
            if q < m:
                trans[state][c] = q

    width = n2 + 1
    total = (n1 + 1) * width * m

    # dp[i, j, k] = maximum length of a valid common subsequence
    # using prefixes s1[:i], s2[:j], ending in KMP state k.
    dp = [-1] * total
    parent = bytearray(total)
    # parent: 1 = skip s1 char, 2 = skip s2 char, 3 = matched char

    dp[0] = 0

    for i in range(n1 + 1):
        row_base = i * width
        i_less = i < n1
        if i_less:
            c1 = s1[i]

        for j2 in range(n2 + 1):
            base = (row_base + j2) * m
            can_match = i_less and j2 < n2 and c1 == s2[j2]
            if can_match:
                cidx = c1 - ord('A')

            for k in range(m):
                cur = dp[base + k]
                if cur < 0:
                    continue

                # Skip s1[i]
                if i_less:
                    nxt = ((i + 1) * width + j2) * m + k
                    if cur > dp[nxt]:
                        dp[nxt] = cur
                        parent[nxt] = 1

                # Skip s2[j2]
                if j2 < n2:
                    nxt = (row_base + j2 + 1) * m + k
                    if cur > dp[nxt]:
                        dp[nxt] = cur
                        parent[nxt] = 2

                # Match s1[i] with s2[j2]
                if can_match:
                    nk = trans[k][cidx]
                    if nk != -1:
                        nxt = ((i + 1) * width + j2 + 1) * m + nk
                        val = cur + 1
                        if val > dp[nxt]:
                            dp[nxt] = val
                            parent[nxt] = 3

    final_base = (n1 * width + n2) * m
    best_len = -1
    best_state = 0

    for k in range(m):
        val = dp[final_base + k]
        if val > best_len:
            best_len = val
            best_state = k

    if best_len <= 0:
        sys.stdout.write("0\n")
        return

    # Reconstruct the answer
    i, j2, k = n1, n2, best_state
    length = best_len
    answer = []

    while length > 0:
        idx = (i * width + j2) * m + k
        p = parent[idx]

        if p == 1:
            i -= 1

        elif p == 2:
            j2 -= 1

        elif p == 3:
            ch = s1[i - 1]
            cidx = ch - ord('A')
            prev_i = i - 1
            prev_j = j2 - 1
            prev_base = (prev_i * width + prev_j) * m
            target = length - 1

            for prev_k in range(m):
                if trans[prev_k][cidx] == k and dp[prev_base + prev_k] == target:
                    answer.append(chr(ch))
                    i, j2, k = prev_i, prev_j, prev_k
                    length -= 1
                    break

    answer.reverse()
    sys.stdout.write("".join(answer) + "\n")


if __name__ == "__main__":
    main()