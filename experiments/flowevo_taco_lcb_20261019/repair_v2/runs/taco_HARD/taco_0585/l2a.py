import sys

MOD = 998244353
MAX_N = 500005

pow2 = [1] * MAX_N
for i in range(1, MAX_N):
    pow2[i] = (pow2[i - 1] * 2) % MOD


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        freq = [0] * (n + 2)

        for _ in range(n):
            x = data[idx]
            idx += 1
            if x <= n + 1:
                freq[x] += 1

        ans = pow2[n]  # k = 0
        product = 1
        prefix_count = 0

        for v in range(1, n + 2):
            c = freq[v]
            if c == 0:
                break

            product = product * (pow2[c] - 1) % MOD
            prefix_count += c

            term = product * pow2[n - prefix_count] % MOD
            ans += term
            if ans >= MOD:
                ans -= MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()