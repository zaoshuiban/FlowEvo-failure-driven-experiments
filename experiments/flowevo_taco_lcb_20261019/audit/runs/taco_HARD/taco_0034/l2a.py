import sys


def solve():
    input = sys.stdin.buffer.readline
    line = input()
    if not line:
        return

    n = int(line)

    qmax_idx = [0] * n
    qmax_val = [0] * n
    qmin_idx = [0] * n
    qmin_val = [0] * n

    hmax = tmax = 0
    hmin = tmin = 0

    left = 0
    answer = 0

    for right in range(n):
        a, b = map(int, input().split())

        while hmax < tmax and qmax_val[tmax - 1] <= a:
            tmax -= 1
        qmax_idx[tmax] = right
        qmax_val[tmax] = a
        tmax += 1

        while hmin < tmin and qmin_val[tmin - 1] >= b:
            tmin -= 1
        qmin_idx[tmin] = right
        qmin_val[tmin] = b
        tmin += 1

        while True:
            length = right - left + 1
            width = qmin_val[hmin] - qmax_val[hmax] + 1

            if width >= length:
                break

            left += 1

            while hmax < tmax and qmax_idx[hmax] < left:
                hmax += 1

            while hmin < tmin and qmin_idx[hmin] < left:
                hmin += 1

        current = right - left + 1
        if current > answer:
            answer = current

    print(answer)


if __name__ == "__main__":
    solve()