import sys

MOD = 1_000_000_007

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    tests = []
    max_den = 1
    idx = 1

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        m = data[idx + 2]
        idx += 3
        tests.append((n, k, m))
        if n > max_den:
            max_den = n
        if n + k > max_den:
            max_den = n + k

    inv = [0] * (max_den + 1)
    inv[1] = 1
    for i in range(2, max_den + 1):
        inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD

    ans_list = []

    for n, k, m in tests:
        fail_first = (n - 1) * inv[n] % MOD

        if m & 1:
            exponent = (m + 1) // 2
            failure = pow(fail_first, exponent, MOD)
        else:
            exponent = m // 2
            fail_second = (n + k - 1) * inv[n + k] % MOD
            failure = pow(fail_first, exponent, MOD) * fail_second % MOD

        answer = (1 - failure) % MOD
        ans_list.append(str(answer))

    sys.stdout.write("\n".join(ans_list))


if __name__ == "__main__":
    main()