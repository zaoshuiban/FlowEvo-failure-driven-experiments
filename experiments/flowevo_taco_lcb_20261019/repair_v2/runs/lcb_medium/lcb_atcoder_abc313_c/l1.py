import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    total = sum(a)
    q, r = divmod(total, n)

    base = 0
    high_count = 0

    for x in a:
        if x > q:
            base += x - q
            high_count += 1

    answer = base - min(r, high_count)
    print(answer)

if __name__ == "__main__":
    main()