import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    a = data[2:2 + n]
    a.sort(reverse=True)

    for days in range(1, n + 1):
        pages = 0
        for i, caffeine in enumerate(a):
            gain = caffeine - i // days
            if gain > 0:
                pages += gain
                if pages >= m:
                    break

        if pages >= m:
            print(days)
            return

    print(-1)

if __name__ == "__main__":
    main()