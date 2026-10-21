import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    positions = [i for i, value in enumerate(a) if value]
    total = len(positions)

    if total == 0:
        print(0)
        return

    if total == 1:
        print(-1)
        return

    prefix = [0] * (total + 1)
    for i, pos in enumerate(positions):
        prefix[i + 1] = prefix[i] + pos

    divisors = []
    d = 1
    while d * d <= total:
        if total % d == 0:
            q = total // d
            if d > 1:
                divisors.append(d)
            if q != d and q > 1:
                divisors.append(q)
        d += 1

    answer = 10**30

    for k in divisors:
        cost = 0
        half = k // 2

        for start in range(0, total, k):
            end = start + k
            mid = start + half
            median = positions[mid]

            left_count = mid - start
            left_cost = median * left_count - (prefix[mid] - prefix[start])

            right_count = end - (mid + 1)
            right_cost = (prefix[end] - prefix[mid + 1]) - median * right_count

            cost += left_cost + right_cost

        answer = min(answer, cost)

    print(answer)


if __name__ == "__main__":
    solve()