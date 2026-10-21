import sys

def solve():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        A = [0] * n
        total = 0

        for i in range(n):
            val = next(it)
            A[i] = val
            if i & 1:
                total -= val
            else:
                total += val

        suffix = 0
        best_gain = 0

        for L in range(n, 0, -1):
            val = A[L - 1]
            signed_val = val if (L & 1) else -val

            if ((n - L) & 1) == 0:
                gain = -2 * suffix
            else:
                gain = -2 * (suffix + signed_val)

            if gain > best_gain:
                best_gain = gain

            suffix += signed_val

        answers.append(str(total + best_gain))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()