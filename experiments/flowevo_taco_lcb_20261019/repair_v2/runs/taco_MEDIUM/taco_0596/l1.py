import sys
import bisect


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    cities = data[2:2 + n]
    towers = data[2 + n:2 + n + m]

    answer = 0

    for city in cities:
        idx = bisect.bisect_left(towers, city)

        best = float("inf")

        if idx < m:
            best = min(best, towers[idx] - city)

        if idx > 0:
            best = min(best, city - towers[idx - 1])

        answer = max(answer, best)

    print(answer)


if __name__ == "__main__":
    main()