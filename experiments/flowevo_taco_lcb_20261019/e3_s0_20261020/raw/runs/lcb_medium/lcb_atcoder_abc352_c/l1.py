import sys

def main():
    input = sys.stdin.readline
    n = int(input())
    total_a = 0
    best = -10**30

    for _ in range(n):
        a, b = map(int, input().split())
        total_a += a
        best = max(best, b - a)

    print(total_a + best)

if __name__ == "__main__":
    main()