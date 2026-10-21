import sys

MOD = 1_000_000_007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ns = data[1:1 + t]

    max_n = max(ns) if ns else 0

    fact = [1] * (max_n + 1)
    for i in range(1, max_n + 1):
        fact[i] = fact[i - 1] * i % MOD

    answers = []
    for n in ns:
        ans = n * (n - 1) % MOD
        ans = ans * fact[n] % MOD
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()