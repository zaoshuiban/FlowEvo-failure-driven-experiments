import sys

def main():
    n, m = map(int, sys.stdin.readline().split())

    points = []

    if n <= m:
        for i in range(n + 1):
            points.append((i, m - i))
    else:
        for i in range(m + 1):
            points.append((n - i, i))

    print(len(points))
    for x, y in points:
        print(x, y)

if __name__ == "__main__":
    main()