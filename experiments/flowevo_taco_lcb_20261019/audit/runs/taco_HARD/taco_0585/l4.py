import sys

MOD = 998244353


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ptr = 1

    tests = []
    max_n = 0

    for _ in range(t):
        n = data[ptr]
        ptr += 1

        arr = data[ptr:ptr + n]
        ptr += n

        tests.append((n, arr))
        if n > max_n:
            max_n = n

    pow2 = [1] * (max_n + 2)
    for i in range(1, max_n + 2):
        pow2[i] = (pow2[i - 1] * 2) % MOD

    answers = []

    for n, arr in tests:
        freq = [0] * (n + 2)

        for a in arr:
            if 1 <= a <= n + 1:
                freq[a] += 1

        # k = 0 contribution: every subsequence contributes at least 1
        ans = pow2[n]

        product = 1
        prefix_count = 0

        for value in range(1, n + 2):
            c = freq[value]
            if c == 0:
                break

            prefix_count += c
            product = product * (pow2[c] - 1) % MOD

            ways = product * pow2[n - prefix_count] % MOD
            ans = (ans + ways) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()