import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    idx = 1

    targets = []
    for _ in range(n):
        x = int(data[idx])
        y = int(data[idx + 1])
        t = int(data[idx + 2])
        p = float(data[idx + 3])
        idx += 4
        targets.append((t, x, y, p))

    targets.sort(key=lambda item: item[0])

    dp = [0.0] * n
    answer = 0.0

    for i in range(n):
        ti, xi, yi, pi = targets[i]
        best = 0.0

        for j in range(i):
            tj, xj, yj, _ = targets[j]

            # Different targets cannot be hit at the same moment.
            if ti == tj:
                continue

            dt = ti - tj
            dx = xi - xj
            dy = yi - yj

            if dx * dx + dy * dy <= dt * dt:
                if dp[j] > best:
                    best = dp[j]

        dp[i] = best + pi
        if dp[i] > answer:
            answer = dp[i]

    print(f"{answer:.10f}")


if __name__ == "__main__":
    main()