import sys

def solve() -> None:
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]
        b = [next(it) for _ in range(n)]

        ans = 0

        for bit in range(29, -1, -1):
            candidate = ans | (1 << bit)

            masked_a = sorted(x & candidate for x in a)
            masked_b = sorted(((x & candidate) ^ candidate) for x in b)

            if masked_a == masked_b:
                ans = candidate

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()