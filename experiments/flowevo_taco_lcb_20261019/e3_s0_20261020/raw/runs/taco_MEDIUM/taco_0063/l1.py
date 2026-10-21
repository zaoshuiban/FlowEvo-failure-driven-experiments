import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    total = sum(a)
    maximum = max(a)

    if total % 2 == 0 and maximum * 2 <= total:
        print("YES")
    else:
        print("NO")

if __name__ == "__main__":
    solve()