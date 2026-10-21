import sys

MOD = 998244353


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    T = int(data[0])
    cases = []
    max_c = 1
    idx = 1

    for _ in range(T):
        s = data[idx]
        K = int(data[idx + 1])
        idx += 2

        n = len(s)
        total = 0
        c = 0

        if K >= 1:
            for i, ch in enumerate(s):
                d = ch - ord('0')
                if d:
                    length = n - i  # position from right + 1
                    total += d * length
                    c += d
            if c > max_c:
                max_c = c

        cases.append((s, K, total, c))

    inv = [0] * (max_c + 2)
    inv[1] = 1
    for i in range(2, max_c + 2):
        inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD

    answers = []

    for s, K, total, c in cases:
        n = len(s)

        if K == 0:
            answers.append(str(n % MOD))
            continue

        if K == 1:
            answers.append(str(total % MOD))
            continue

        r = K - 1

        ans = 0
        weight = 1
        t = 1
        remaining = total % MOD

        for i, ch in enumerate(s):
            d = ch - ord('0')
            if d == 0:
                continue

            length = n - i

            for _ in range(d):
                ans = (ans + weight * remaining) % MOD

                # weight for the next 1
                weight = weight * ((r + t - 1) % MOD) % MOD
                weight = weight * inv[t] % MOD

                t += 1
                remaining -= length
                if remaining < 0:
                    remaining += MOD

        answers.append(str(ans % MOD))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()