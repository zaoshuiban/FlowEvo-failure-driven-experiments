import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]

    instruments = sorted((days, idx + 1) for idx, days in enumerate(a))

    selected = []
    total_days = 0

    for days, idx in instruments:
        if total_days + days <= k:
            total_days += days
            selected.append(idx)
        else:
            break

    output = [
        str(len(selected)),
        " ".join(map(str, selected))
    ]
    sys.stdout.write("\n".join(output) + "\n")

if __name__ == "__main__":
    main()