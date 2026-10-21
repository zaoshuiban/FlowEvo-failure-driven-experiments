import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    D = data[1]

    workers = []
    idx = 2
    for _ in range(n):
        T = data[idx]
        X = data[idx + 1]
        Y = data[idx + 2]
        idx += 3
        workers.append((T, X, Y))

    workers.sort()

    remaining = D
    cost = 0
    current_speed = 0
    current_time = 0

    i = 0
    while i < n:
        t = workers[i][0]

        if current_speed > 0:
            painted = current_speed * (t - current_time)
            if painted >= remaining:
                print(cost)
                return
            remaining -= painted

        max_speed = -1
        min_cost = 10**18

        j = i
        while j < n and workers[j][0] == t:
            _, x, y = workers[j]
            if y > max_speed:
                max_speed = y
                min_cost = x
            elif y == max_speed and x < min_cost:
                min_cost = x
            j += 1

        if max_speed > current_speed:
            cost += min_cost
            current_speed = max_speed

        current_time = t
        i = j

    print(cost)


if __name__ == "__main__":
    main()