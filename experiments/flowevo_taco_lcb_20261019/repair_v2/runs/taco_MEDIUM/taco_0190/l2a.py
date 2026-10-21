import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, D = data[0], data[1]

    workers = []
    idx = 2
    for _ in range(n):
        t, x, y = data[idx], data[idx + 1], data[idx + 2]
        idx += 3
        # Sort by time ascending, speed descending, cost ascending.
        workers.append((t, -y, x))

    workers.sort()

    ans = 0
    current_time = None
    current_speed = 0
    painted = 0

    i = 0
    while i < n:
        t = workers[i][0]

        if current_time is not None:
            painted += current_speed * (t - current_time)

            # The earliest possible finish is already reached before/at time t,
            # so workers available at time t are not needed.
            if painted >= D:
                print(ans)
                return

        # The first worker in this time group after sorting has the maximum speed
        # at time t, and among those with that maximum speed, the minimum cost.
        max_speed = -workers[i][1]
        min_cost = workers[i][2]

        # Skip all workers with the same availability time.
        j = i + 1
        while j < n and workers[j][0] == t:
            j += 1

        if max_speed > current_speed:
            ans += min_cost
            current_speed = max_speed

        current_time = t
        i = j

    # After the last release time, the current maximum speed continues forever.
    print(ans)


if __name__ == "__main__":
    solve()