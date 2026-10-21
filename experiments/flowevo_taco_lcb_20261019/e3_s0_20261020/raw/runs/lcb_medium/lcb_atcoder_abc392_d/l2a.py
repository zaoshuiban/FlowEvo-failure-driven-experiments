import sys

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    idx = 1

    ks = [0] * n
    occurrences = {}

    for i in range(n):
        k = data[idx]
        idx += 1
        ks[i] = k

        counts = {}
        end = idx + k
        while idx < end:
            a = data[idx]
            counts[a] = counts.get(a, 0) + 1
            idx += 1

        for value, count in counts.items():
            if value not in occurrences:
                occurrences[value] = []
            occurrences[value].append((i, count))

    dot = [[0] * n for _ in range(n)]

    for lst in occurrences.values():
        m = len(lst)
        for a in range(m):
            i, ci = lst[a]
            row = dot[i]
            for b in range(a + 1, m):
                j, cj = lst[b]
                row[j] += ci * cj

    answer = 0.0

    for i in range(n):
        for j in range(i + 1, n):
            prob = dot[i][j] / (ks[i] * ks[j])
            if prob > answer:
                answer = prob

    print(f"{answer:.15f}")


if __name__ == "__main__":
    main()