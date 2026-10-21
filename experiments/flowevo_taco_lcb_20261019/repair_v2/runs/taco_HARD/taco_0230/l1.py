import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    total = sum(a)
    floor_avg = total // n
    ceil_avg = (total + n - 1) // n

    a.sort()

    # Find the maximum possible minimum wealth after k days.
    rem = k
    L = 0
    for i in range(n - 1):
        if a[i] == a[i + 1]:
            continue

        cnt = i + 1
        cost = (a[i + 1] - a[i]) * cnt

        if cost > rem:
            L = a[i] + rem // cnt
            break

        rem -= cost
    else:
        L = a[-1] + rem // n

    if L > floor_avg:
        L = floor_avg

    # Find the minimum possible maximum wealth after k days.
    rem = k
    R = 0
    for i in range(n - 1, 0, -1):
        if a[i] == a[i - 1]:
            continue

        cnt = n - i
        cost = (a[i] - a[i - 1]) * cnt

        if cost > rem:
            R = a[i] - rem // cnt
            break

        rem -= cost
    else:
        R = a[0] - rem // n

    if R < ceil_avg:
        R = ceil_avg

    print(R - L)


if __name__ == "__main__":
    solve()