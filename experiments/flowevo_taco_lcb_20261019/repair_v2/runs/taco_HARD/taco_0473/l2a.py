import sys

MOD = 1_000_000_007
MAX = 60_005

# Precompute modular inverses
inv = [0] * MAX
inv[1] = 1
for i in range(2, MAX):
    inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        m = data[idx + 2]
        idx += 3

        # Failure probability of one guess from n boxes:
        # (n - 1) / n
        fail_once = (n - 1) * inv[n] % MOD

        # Number of guesses at the initial n boxes, with resets between them
        guesses = (m + 1) // 2

        failure_prob = pow(fail_once, guesses, MOD)

        # If m is even, one final additional guess is made after n has become n + k
        if m % 2 == 0:
            nk = n + k
            extra_fail = (nk - 1) * inv[nk] % MOD
            failure_prob = failure_prob * extra_fail % MOD

        answer = (1 - failure_prob) % MOD
        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()