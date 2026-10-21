import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, D = data[0], data[1]
    workers = []
    p = 2
    for _ in range(n):
        t, x, y = data[p], data[p + 1], data[p + 2]
        p += 3
        workers.append((t, x, y))

    workers.sort()

    remaining = D
    current_time = 0
    current_speed = 0
    answer = 0

    i = 0
    INF = 10**18

    while i < n:
        t = workers[i][0]

        # Paint until time t using the current fastest hired worker.
        if current_speed > 0:
            can_paint = current_speed * (t - current_time)
            if remaining <= can_paint:
                print(answer)
                return
            remaining -= can_paint

        current_time = t

        # Find the maximum speed becoming available at this exact time,
        # and the minimum hiring cost among workers with that speed.
        max_speed = 0
        min_cost = INF

        while i < n and workers[i][0] == t:
            _, cost, speed = workers[i]

            if speed > max_speed:
                max_speed = speed
                min_cost = cost
            elif speed == max_speed:
                if cost < min_cost:
                    min_cost = cost

            i += 1

        # If this gives a new maximum speed, it must be hired for the
        # earliest possible completion time.
        if max_speed > current_speed:
            current_speed = max_speed
            answer += min_cost

    print(answer)


if __name__ == "__main__":
    solve()