import sys


def main():
    data = sys.stdin.read().split()
    s1 = data[0].encode()
    s2 = data[1].encode()
    virus = data[2].encode()

    n1 = len(s1)
    n2 = len(s2)
    m = len(virus)

    # KMP prefix function for virus
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and virus[i] != virus[j]:
            j = pi[j - 1]
        if virus[i] == virus[j]:
            j += 1
        pi[i] = j

    # KMP automaton transitions.
    # State k means the current string has suffix equal to virus[:k].
    # trans[k][c] = next state, or -1 if appending character c creates virus.
    trans = [[-1] * 26 for _ in range(m)]

    for k in range(m):
        row = trans[k]
        for c in range(26):
            ch = 65 + c
            q = k

            while q > 0 and virus[q] != ch:
                q = pi[q - 1]

            if virus[q] == ch:
                q += 1

            if q < m:
                row[c] = q

    # dp[i][j][k] = maximum length of a valid common subsequence
    # using prefixes s1[:i], s2[:j], ending in automaton state k.
    # 255 means unreachable.
    width = n2 + 1
    total = (n1 + 1) * (n2 + 1) * m
    dp = bytearray([255]) * total
    dp[0] = 0

    for i in range(n1 + 1):
        iw = i * width

        c1 = s1[i] if i < n1 else -1
        cidx1 = c1 - 65 if i < n1 else -1

        for j2 in range(n2 + 1):
            base = (iw + j2) * m

            can_match = i < n1 and j2 < n2 and c1 == s2[j2]
            cidx = cidx1 if can_match else -1

            for k in range(m):
                cur = dp[base + k]
                if cur == 255:
                    continue

                # Skip character s1[i]
                if i < n1:
                    nxt = ((i + 1) * width + j2) * m + k
                    old = dp[nxt]
                    if old == 255 or cur > old:
                        dp[nxt] = cur

                # Skip character s2[j2]
                if j2 < n2:
                    nxt = (iw + j2 + 1) * m + k
                    old = dp[nxt]
                    if old == 255 or cur > old:
                        dp[nxt] = cur

                # Match s1[i] with s2[j2]
                if can_match:
                    nk = trans[k][cidx]
                    if nk != -1:
                        nxt = ((i + 1) * width + j2 + 1) * m + nk
                        val = cur + 1
                        old = dp[nxt]
                        if old == 255 or val > old:
                            dp[nxt] = val

    final_base = (n1 * width + n2) * m
    best_len = -1
    best_state = 0

    for k in range(m):
        val = dp[final_base + k]
        if val != 255 and val > best_len:
            best_len = val
            best_state = k

    if best_len <= 0:
        sys.stdout.write("0\n")
        return

    # Reconstruct the answer.
    i = n1
    j2 = n2
    k = best_state
    length = best_len
    answer = []

    while length > 0:
        moved = False

        # Try skipping a character from s1.
        if i > 0:
            prev = ((i - 1) * width + j2) * m + k
            if dp[prev] == length:
                i -= 1
                moved = True

        # Try skipping a character from s2.
        if not moved and j2 > 0:
            prev = (i * width + (j2 - 1)) * m + k
            if dp[prev] == length:
                j2 -= 1
                moved = True

        if moved:
            continue

        # Otherwise, the current state must have been reached by matching.
        ch = s1[i - 1]
        cidx = ch - 65
        prev_i = i - 1
        prev_j = j2 - 1
        prev_base = (prev_i * width + prev_j) * m
        target = length - 1

        for prev_k in range(m):
            if trans[prev_k][cidx] == k and dp[prev_base + prev_k] == target:
                answer.append(chr(ch))
                i = prev_i
                j2 = prev_j
                k = prev_k
                length -= 1
                break

    answer.reverse()
    sys.stdout.write("".join(answer) + "\n")


if __name__ == "__main__":
    main()