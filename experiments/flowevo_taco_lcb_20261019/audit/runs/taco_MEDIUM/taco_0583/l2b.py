import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    q = next(it)
    answers = []

    for _ in range(q):
        n = next(it)
        temperature = next(it)

        low = high = temperature
        prev_time = 0
        possible = True

        for _ in range(n):
            t = next(it)
            l = next(it)
            h = next(it)

            if possible:
                dt = t - prev_time
                low -= dt
                high += dt

                low = max(low, l)
                high = min(high, h)

                if low > high:
                    possible = False

                prev_time = t

        answers.append("YES" if possible else "NO")

    print("\n".join(answers))


if __name__ == "__main__":
    solve()