import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    pos = [i for i, value in enumerate(a) if value == 1]
    total_pieces = len(pos)

    if total_pieces <= 1:
        print(-1)
        return

    # Distinct prime factors of total_pieces
    x = total_pieces
    primes = []
    d = 2
    while d * d <= x:
        if x % d == 0:
            primes.append(d)
            while x % d == 0:
                x //= d
        d += 1
    if x > 1:
        primes.append(x)

    prefix = [0] * (total_pieces + 1)
    for i, p in enumerate(pos):
        prefix[i + 1] = prefix[i] + p

    answer = 10**30

    for group_size in primes:
        cost = 0
        left = 0

        while left < total_pieces:
            right = left + group_size - 1
            mid = left + group_size // 2
            median = pos[mid]

            left_cost = median * (mid - left) - (prefix[mid] - prefix[left])
            right_cost = (prefix[right + 1] - prefix[mid + 1]) - median * (right - mid)

            cost += left_cost + right_cost
            left += group_size

        answer = min(answer, cost)

    print(answer)


if __name__ == "__main__":
    solve()