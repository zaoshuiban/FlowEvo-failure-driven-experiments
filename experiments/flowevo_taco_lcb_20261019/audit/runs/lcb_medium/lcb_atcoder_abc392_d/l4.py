import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    n = data[idx]
    idx += 1

    dice = []

    for _ in range(n):
        k = data[idx]
        idx += 1

        counts = {}
        for _ in range(k):
            a = data[idx]
            idx += 1
            counts[a] = counts.get(a, 0) + 1

        dice.append((counts, k))

    best = 0.0

    for i in range(n):
        counts_i, k_i = dice[i]

        for j in range(i + 1, n):
            counts_j, k_j = dice[j]

            if len(counts_i) <= len(counts_j):
                match = 0
                get_j = counts_j.get
                for value, cnt in counts_i.items():
                    match += cnt * get_j(value, 0)
            else:
                match = 0
                get_i = counts_i.get
                for value, cnt in counts_j.items():
                    match += cnt * get_i(value, 0)

            prob = match / (k_i * k_j)
            if prob > best:
                best = prob

    print(f"{best:.15f}")


if __name__ == "__main__":
    main()