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

    # KMP automaton.
    # trans[state][c] = next state, or -1 if appending c creates virus.
    trans = [[-1] * 26 for _ in range(m)]
    for state in range(m):
        for c in range(26):
            ch = 65 + c  # 'A'
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
    prev_state = bytearray(total)

    # parent values:
    # 1 = skip s1 character
    # 2 = skip s2 character
    # 3 = match current characters
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
                cidx = c1 - 65

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
                            prev_state[nxt] = k

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

    # Reconstruct the answer.
    i, j2, k = n1, n2, best_state
    answer = []

    while True:
        idx = (i * width + j2) * m + k
        p = parent[idx]

        if p == 0:
            break
        elif p == 1:
            i -= 1
        elif p == 2:
            j2 -= 1
        else:
            answer.append(chr(s1[i - 1]))
            k = prev_state[idx]
            i -= 1
            j2 -= 1

    answer.reverse()
    sys.stdout.write("".join(answer) + "\n")


if __name__ == "__main__":
    main()