import sys
import bisect

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, M, D = data[0], data[1], data[2]

    A = data[3:3 + N]
    B = data[3 + N:3 + N + M]

    B.sort()

    ans = -1

    for a in A:
        idx = bisect.bisect_right(B, a + D) - 1

        if idx >= 0 and B[idx] >= a - D:
            ans = max(ans, a + B[idx])

    print(ans)

if __name__ == "__main__":
    main()