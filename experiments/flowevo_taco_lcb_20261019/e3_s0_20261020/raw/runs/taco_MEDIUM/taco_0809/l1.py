import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        A = [next(it) for _ in range(n)]
        B = [next(it) for _ in range(n)]

        freq = {}
        ans = 0

        for a, b in zip(A, B):
            # Need previous i such that:
            # A[i] = B[j] = b
            # B[i] = A[j] = a
            ans += freq.get((b, a), 0)

            # Insert current pair (A[j], B[j])
            key = (a, b)
            freq[key] = freq.get(key, 0) + 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()