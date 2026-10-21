import sys

def main():
    input = sys.stdin.readline
    n = int(input())

    covered = [[False] * 100 for _ in range(100)]

    for _ in range(n):
        a, b, c, d = map(int, input().split())
        for x in range(a, b):
            for y in range(c, d):
                covered[x][y] = True

    area = sum(sum(row) for row in covered)
    print(area)

if __name__ == "__main__":
    main()