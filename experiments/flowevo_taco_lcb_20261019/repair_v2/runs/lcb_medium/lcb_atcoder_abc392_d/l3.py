import sys
from collections import defaultdict

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    n = data[idx]
    idx += 1

    ks = []
    by_value = defaultdict(list)

    for i in range(n):
        k = data[idx]
        idx += 1
        ks.append(k)

        count = {}
        for _ in range(k):
            a = data[idx]
            idx += 1
            count[a] = count.get(a, 0) + 1

        for value, cnt in count.items():
            by_value[value].append((i, cnt))

    pair_match = [[0] * n for _ in range(n)]

    for lst in by_value.values():
        m = len(lst)
        for p in range(m):
            i, ci = lst[p]
            for q in range(p + 1, m):
                j, cj = lst[q]
                if i < j:
                    pair_match[i][j] += ci * cj
                else:
                    pair_match[j][i] += ci * cj

    best = 0.0

    for i in range(n):
        for j in range(i + 1, n):
            prob = pair_match[i][j] / (ks[i] * ks[j])
            if prob > best:
                best = prob

    print(f"{best:.15f}")


if __name__ == "__main__":
    main()