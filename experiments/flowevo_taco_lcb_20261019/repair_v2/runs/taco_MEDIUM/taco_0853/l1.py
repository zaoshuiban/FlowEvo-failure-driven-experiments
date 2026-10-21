import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    m = next(it)

    a = [[0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            a[i][j] = next(it)

    low = [[0] * m for _ in range(n)]
    high = [[0] * m for _ in range(n)]

    for i in range(n):
        for j in range(m):
            b = next(it)
            x = a[i][j]
            low[i][j] = min(x, b)
            high[i][j] = max(x, b)

    for i in range(n):
        for j in range(m - 1):
            if not (low[i][j] < low[i][j + 1] and high[i][j] < high[i][j + 1]):
                print("Impossible")
                return

    for i in range(n - 1):
        for j in range(m):
            if not (low[i][j] < low[i + 1][j] and high[i][j] < high[i + 1][j]):
                print("Impossible")
                return

    print("Possible")


if __name__ == "__main__":
    main()