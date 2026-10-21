import sys
import bisect

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    M = next(it)

    A = [next(it) for _ in range(N)]
    B = [next(it) for _ in range(M)]

    A.sort()
    B.sort()

    low = 1
    high = max(B) + 1

    while low < high:
        mid = (low + high) // 2

        sellers = bisect.bisect_right(A, mid)
        buyers = M - bisect.bisect_left(B, mid)

        if sellers >= buyers:
            high = mid
        else:
            low = mid + 1

    print(low)

if __name__ == "__main__":
    main()