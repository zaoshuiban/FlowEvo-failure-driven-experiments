import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    instruments = sorted((a[i], i + 1) for i in range(n))

    chosen = []
    total = 0

    for days, index in instruments:
        if total + days <= k:
            total += days
            chosen.append(index)
        else:
            break

    print(len(chosen))
    if chosen:
        print(*chosen)

if __name__ == "__main__":
    main()