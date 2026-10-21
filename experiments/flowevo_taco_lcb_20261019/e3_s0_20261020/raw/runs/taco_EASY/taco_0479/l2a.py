import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, d = data[0], data[1]
    x = data[2:2 + n]

    ans = 0
    left = 0

    for right in range(n):
        while x[right] - x[left] > d:
            left += 1

        count = right - left
        ans += count * (count - 1) // 2

    print(ans)

if __name__ == "__main__":
    main()