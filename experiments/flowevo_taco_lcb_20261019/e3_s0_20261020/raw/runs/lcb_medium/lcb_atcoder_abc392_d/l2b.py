import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    dice = []

    for _ in range(n):
        k = next(it)
        counts = {}
        for _ in range(k):
            a = next(it)
            counts[a] = counts.get(a, 0) + 1
        dice.append((k, counts))

    best = 0.0

    for i in range(n):
        ki, ci = dice[i]
        for j in range(i + 1, n):
            kj, cj = dice[j]

            numerator = 0

            if len(ci) <= len(cj):
                for value, count_i in ci.items():
                    count_j = cj.get(value)
                    if count_j is not None:
                        numerator += count_i * count_j
            else:
                for value, count_j in cj.items():
                    count_i = ci.get(value)
                    if count_i is not None:
                        numerator += count_i * count_j

            probability = numerator / (ki * kj)
            if probability > best:
                best = probability

    print(f"{best:.15f}")


if __name__ == "__main__":
    main()