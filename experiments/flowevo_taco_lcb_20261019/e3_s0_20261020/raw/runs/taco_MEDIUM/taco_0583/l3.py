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
        temperature = data[idx + 1]
        idx += 2

        low = high = temperature
        prev_time = 0
        possible = True

        for _ in range(n):
            t = data[idx]
            l = data[idx + 1]
            h = data[idx + 2]
            idx += 3

            dt = t - prev_time
            low -= dt
            high += dt

            low = max(low, l)
            high = min(high, h)

            if low > high:
                possible = False

            prev_time = t

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()