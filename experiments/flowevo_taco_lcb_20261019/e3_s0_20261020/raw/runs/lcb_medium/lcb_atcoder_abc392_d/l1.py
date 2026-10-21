import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)

    counts = []
    sizes = []

    for _ in range(N):
        k = next(it)
        freq = {}
        for _ in range(k):
            a = next(it)
            freq[a] = freq.get(a, 0) + 1
        counts.append(freq)
        sizes.append(k)

    best = 0.0

    for i in range(N):
        ci = counts[i]
        ki = sizes[i]

        for j in range(i + 1, N):
            cj = counts[j]
            kj = sizes[j]

            common = 0

            if len(ci) <= len(cj):
                for value, cnt in ci.items():
                    other = cj.get(value)
                    if other is not None:
                        common += cnt * other
            else:
                for value, cnt in cj.items():
                    other = ci.get(value)
                    if other is not None:
                        common += cnt * other

            probability = common / (ki * kj)

            if probability > best:
                best = probability

    print(f"{best:.15f}")

if __name__ == "__main__":
    main()