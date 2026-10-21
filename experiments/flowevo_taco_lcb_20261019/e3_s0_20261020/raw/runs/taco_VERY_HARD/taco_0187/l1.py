import sys

MOD = 1_000_000_007
ALPHABET = 26

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        s = data[idx + 1]
        idx += 2

        m = len(s)

        if n <= m:
            answers.append("0")
            continue

        k = n - m  # length of the deleted substring

        # Answer = 26^(k-1) * (26 + 25*m) mod MOD
        factor = (ALPHABET + (m % MOD) * (ALPHABET - 1)) % MOD
        ans = pow(ALPHABET, k - 1, MOD) * factor % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()