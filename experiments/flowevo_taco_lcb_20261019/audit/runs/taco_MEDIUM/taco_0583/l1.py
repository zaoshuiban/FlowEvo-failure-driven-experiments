import sys


def solve() -> None:
    data = iter(map(int, sys.stdin.buffer.read().split()))
    q = next(data)
    answers = []

    for _ in range(q):
        n = next(data)
        temperature = next(data)

        low = high = temperature
        current_time = 0
        possible = True

        for _ in range(n):
            t = next(data)
            l = next(data)
            h = next(data)

            if not possible:
                continue

            dt = t - current_time
            low -= dt
            high += dt

            low = max(low, l)
            high = min(high, h)

            if low > high:
                possible = False

            current_time = t

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()