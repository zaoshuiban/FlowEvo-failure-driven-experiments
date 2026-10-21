import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    instruments = sorted((a[i], i + 1) for i in range(n))

    selected = []
    total_days = 0

    for days, idx in instruments:
        if total_days + days <= k:
            total_days += days
            selected.append(idx)

    print(len(selected))
    print(*selected)

if __name__ == "__main__":
    main()