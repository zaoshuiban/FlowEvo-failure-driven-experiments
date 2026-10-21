import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    queries = data[1:1 + t]
    max_n = max(queries) if queries else 0

    # Kahan summation for harmonic numbers
    h = [0.0] * (max_n + 1)
    s = 0.0
    c = 0.0

    for i in range(1, max_n + 1):
        y = 1.0 / i - c
        t_val = s + y
        c = (t_val - s) - y
        s = t_val
        h[i] = s - c

    out = []

    for n in queries:
        if n == 1:
            out.append("0.00000000000")
            continue

        # Binary search for the optimal lambda in:
        # p_i = max(0, (i - lambda) / (2i))
        lo = 0.0
        hi = float(n)

        for _ in range(75):
            mid = (lo + hi) * 0.5
            k = int(mid)
            if k > n:
                k = n

            inv_sum = h[n] - h[k]
            total_prob = 0.5 * ((n - k) - mid * inv_sum)

            if total_prob > 1.0:
                lo = mid
            else:
                hi = mid

        lam = (lo + hi) * 0.5
        k = int(lam)
        if k < 0:
            k = 0
        elif k > n:
            k = n

        inv_sum = h[n] - h[k]
        cnt = n - k

        # Sum of indices from k+1 to n
        index_sum = (k + 1 + n) * cnt * 0.5

        expected_score = 0.5 * (index_sum - lam * lam * inv_sum)
        max_score = 2.0 * n - 1.0
        ratio = expected_score / max_score

        out.append(f"{ratio:.11f}")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()