import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    q = next(it)
    answers = []

    for _ in range(q):
        n = next(it)
        m = next(it)

        low = high = m
        prev_time = 0
        possible = True

        for _ in range(n):
            t = next(it)
            l = next(it)
            h = next(it)

            elapsed = t - prev_time
            low -= elapsed
            high += elapsed

            low = max(low, l)
            high = min(high, h)

            if low > high:
                possible = False

            prev_time = t

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()