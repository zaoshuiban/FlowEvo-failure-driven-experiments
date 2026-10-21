import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    ans = n  # All length-1 subsequences are arithmetic progressions.

    if n >= 2:
        prev_diff = a[1] - a[0]
        run = 1

        for i in range(2, n):
            diff = a[i] - a[i - 1]
            if diff == prev_diff:
                run += 1
            else:
                ans += run * (run + 1) // 2
                prev_diff = diff
                run = 1

        ans += run * (run + 1) // 2

    print(ans)

if __name__ == "__main__":
    main()