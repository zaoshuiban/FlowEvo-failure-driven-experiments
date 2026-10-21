import sys

def main():
    n, p = map(int, sys.stdin.buffer.readline().split())

    for k in range(1, 31):
        s = n - k * p
        if s <= 0:
            continue

        if s.bit_count() <= k <= s:
            print(k)
            return

    print(-1)

if __name__ == "__main__":
    main()