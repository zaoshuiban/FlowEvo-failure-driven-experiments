import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    x = data[1:1 + n]

    ans = 0
    limit = max(max(x), n) + 1

    for d in range(1, limit + 1):
        cnt = sum(v < d for v in x)
        ans = max(ans, (cnt + d - 1) // d)

    print(ans)

if __name__ == "__main__":
    main()