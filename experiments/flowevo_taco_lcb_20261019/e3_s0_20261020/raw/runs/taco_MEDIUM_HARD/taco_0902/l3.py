import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    p = int(data[1])

    k = 1
    while True:
        s = n - k * p

        if s <= 0:
            print(-1)
            return

        if s.bit_count() <= k <= s:
            print(k)
            return

        if k > s:
            print(-1)
            return

        k += 1

if __name__ == "__main__":
    main()