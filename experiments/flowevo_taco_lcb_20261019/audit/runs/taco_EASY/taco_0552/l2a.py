import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    instruments = sorted((days, idx + 1) for idx, days in enumerate(a))

    chosen = []
    total = 0

    for days, idx in instruments:
        if total + days <= k:
            total += days
            chosen.append(idx)
        else:
            break

    print(len(chosen))
    print(*chosen)

if __name__ == "__main__":
    main()