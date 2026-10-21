import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    q = data[0]
    idx = 1
    answers = []

    for _ in range(q):
        n = data[idx]
        initial_temp = data[idx + 1]
        idx += 2

        customers = []
        for _ in range(n):
            t = data[idx]
            l = data[idx + 1]
            h = data[idx + 2]
            idx += 3
            customers.append((t, l, h))

        customers.sort()

        low = high = initial_temp
        prev_time = 0
        possible = True

        for t, l, h in customers:
            dt = t - prev_time

            low -= dt
            high += dt

            low = max(low, l)
            high = min(high, h)

            if low > high:
                possible = False
                break

            prev_time = t

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()