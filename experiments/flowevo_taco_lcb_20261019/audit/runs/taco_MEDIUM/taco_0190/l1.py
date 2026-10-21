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
        workers.append((t, x, y))

    workers.sort(key=lambda w: w[0])

    ans = 0
    remaining = D
    current_speed = 0
    prev_time = None

    i = 0
    finished = False

    while i < n and not finished:
        t = workers[i][0]

        max_y = -1
        min_cost = 10**18
        j = i

        while j < n and workers[j][0] == t:
            _, cost, speed = workers[j]

            if speed > max_y:
                max_y = speed
                min_cost = cost
            elif speed == max_y and cost < min_cost:
                min_cost = cost

            j += 1

        if max_y > current_speed:
            if current_speed == 0:
                ans += min_cost
                current_speed = max_y
                prev_time = t
            else:
                area = current_speed * (t - prev_time)

                if remaining <= area:
                    finished = True
                    break

                remaining -= area
                ans += min_cost
                current_speed = max_y
                prev_time = t

        i = j

    print(ans)


if __name__ == "__main__":
    solve()