import sys


def solve():
    data = sys.stdin.read().split()
    if len(data) < 3:
        return

    s1, s2, virus = data[0], data[1], data[2]

    n, m = len(s1), len(s2)
    v = len(virus)

    # KMP prefix function for virus
    pi = [0] * v
    for i in range(1, v):
        j = pi[i - 1]
        while j > 0 and virus[i] != virus[j]:
            j = pi[j - 1]
        if virus[i] == virus[j]:
            j += 1
        pi[i] = j

    # trans[k][c]: state after adding character c to current matched prefix length k
    trans = [[0] * 26 for _ in range(v)]

    for k in range(v):
        for c in range(26):
            ch = chr(ord('A') + c)
            q = k

            while q > 0 and virus[q] != ch:
                q = pi[q - 1]

            if virus[q] == ch:
                q += 1

            trans[k][c] = q

    # dp[i][j][k] = maximum additional common subsequence length
    # from s1[i:], s2[j:], with current virus-prefix match length k.
    width = v
    row_stride = (m + 1) * width
    dp = bytearray((n + 1) * row_stride)

    for i in range(n - 1, -1, -1):
        base_i = i * row_stride
        base_i1 = (i + 1) * row_stride
        ch1 = s1[i]
        char_index = ord(ch1) - ord('A')

        for j in range(m - 1, -1, -1):
            idx = base_i + j * width
            down = base_i1 + j * width
            right = base_i + (j + 1) * width

            if ch1 == s2[j]:
                take_base = base_i1 + (j + 1) * width

                for k in range(width):
                    best = dp[down + k]
                    val = dp[right + k]
                    if val > best:
                        best = val

                    next_k = trans[k][char_index]
                    if next_k < v:
                        val = 1 + dp[take_base + next_k]
                        if val > best:
                            best = val

                    dp[idx + k] = best
            else:
                for k in range(width):
                    best = dp[down + k]
                    val = dp[right + k]
                    if val > best:
                        best = val

                    dp[idx + k] = best

    # Reconstruct one optimal answer
    answer = []
    i = j = k = 0

    while i < n and j < m:
        cur = dp[i * row_stride + j * width + k]
        if cur == 0:
            break

        # Try taking s1[i] == s2[j]
        if s1[i] == s2[j]:
            char_index = ord(s1[i]) - ord('A')
            next_k = trans[k][char_index]

            if next_k < v:
                next_value = 1 + dp[(i + 1) * row_stride + (j + 1) * width + next_k]
                if next_value == cur:
                    answer.append(s1[i])
                    i += 1
                    j += 1
                    k = next_k
                    continue

        # Skip s1[i]
        if dp[(i + 1) * row_stride + j * width + k] == cur:
            i += 1
            continue

        # Skip s2[j]
        if dp[i * row_stride + (j + 1) * width + k] == cur:
            j += 1
            continue

        break

    if answer:
        print(''.join(answer))
    else:
        print(0)


if __name__ == "__main__":
    solve()