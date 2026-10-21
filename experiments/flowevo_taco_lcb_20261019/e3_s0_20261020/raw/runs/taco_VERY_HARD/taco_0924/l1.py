import sys

MOD = 1000000007
SMALL_INDEX = {2: 0, 3: 1, 5: 2, 7: 3}


def build_info(limit=100):
    spf = list(range(limit + 1))
    for i in range(2, int(limit ** 0.5) + 1):
        if spf[i] == i:
            for j in range(i * i, limit + 1, i):
                if spf[j] == j:
                    spf[j] = i

    infos = [(0, 0)] * (limit + 1)

    for n in range(2, limit + 1):
        x = n
        mask = 0
        large_prime = 0

        while x > 1:
            p = spf[x]

            if p in SMALL_INDEX:
                mask |= 1 << SMALL_INDEX[p]
            else:
                large_prime = p

            while x % p == 0:
                x //= p

        infos[n] = (mask, large_prime)

    return infos


def count_coefficients(m, infos):
    small_count = [0] * 16
    large_counts = {}

    for n in range(2, m + 1):
        mask, large_prime = infos[n]

        if large_prime == 0:
            small_count[mask] += 1
        else:
            if large_prime not in large_counts:
                large_counts[large_prime] = [0] * 16
            large_counts[large_prime][mask] += 1

    max_len = m + 2
    dp = [[0] * max_len for _ in range(16)]
    dp[0][0] = 1

    for support in range(1, 16):
        cnt = small_count[support]
        if cnt == 0:
            continue

        new_dp = [row[:] for row in dp]

        for mask in range(16):
            if mask & support:
                continue

            src = dp[mask]
            dest = new_dp[mask | support]

            for k in range(m + 1):
                if src[k]:
                    dest[k + 1] = (dest[k + 1] + src[k] * cnt) % MOD

        dp = new_dp

    for p in sorted(large_counts):
        options = large_counts[p]
        new_dp = [row[:] for row in dp]

        for mask in range(16):
            src = dp[mask]

            for support in range(16):
                cnt = options[support]

                if cnt == 0 or (mask & support):
                    continue

                dest = new_dp[mask | support]

                for k in range(m + 1):
                    if src[k]:
                        dest[k + 1] = (dest[k + 1] + src[k] * cnt) % MOD

        dp = new_dp

    coeff = [0] * max_len

    for mask in range(16):
        for k in range(max_len):
            coeff[k] = (coeff[k] + dp[mask][k]) % MOD

    return coeff


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1

    infos = build_info(100)
    cache = {}
    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        if m not in cache:
            cache[m] = count_coefficients(m, infos)

        coeff = cache[m]

        ans = 0
        falling = 1

        for k, ways in enumerate(coeff):
            if k == 0:
                falling = 1
            else:
                if k > n:
                    break
                falling = falling * ((n - k + 1) % MOD) % MOD

            ans = (ans + ways * falling) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()