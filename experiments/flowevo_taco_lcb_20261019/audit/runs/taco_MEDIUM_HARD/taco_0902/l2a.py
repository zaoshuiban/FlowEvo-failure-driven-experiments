import sys

def main():
    n, p = map(int, sys.stdin.buffer.readline().split())

    for k in range(1, 1001):
        m = n - p * k
        if m >= k and m.bit_count() <= k:
            print(k)
            return

    print(-1)

if __name__ == "__main__":
    main()