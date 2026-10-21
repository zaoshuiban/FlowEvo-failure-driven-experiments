import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    n = int(next(it))

    targets = []
    for _ in range(n):
        x = int(next(it))
        y = int(next(it))
        t = int(next(it))
        p = float(next(it))
        targets.append((t, x, y, p))

    targets.sort(key=lambda v: v[0])

    dp = [0.0] * n
    answer = 0.0

    for i in range(n):
        ti, xi, yi, pi = targets[i]
        best_prev = 0.0

        for j in range(i):
            tj, xj, yj, _ = targets[j]

            dt = ti - tj
            if dt < 0:
                continue

            dx = xi - xj
            dy = yi - yj

            if dx * dx + dy * dy <= dt * dt:
                if dp[j] > best_prev:
                    best_prev = dp[j]

        dp[i] = best_prev + pi
        if dp[i] > answer:
            answer = dp[i]

    print(f"{answer:.10f}")


if __name__ == "__main__":
    solve()