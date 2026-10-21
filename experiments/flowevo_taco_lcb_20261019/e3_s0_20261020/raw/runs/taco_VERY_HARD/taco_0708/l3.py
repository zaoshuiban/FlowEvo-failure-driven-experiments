import sys

def main() -> None:
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    grid = data[2:2 + n]

    a = [[1 if ch == 'B' else 0 for ch in row] for row in grid]

    e = [[0] * m for _ in range(n)]
    weight = 0

    for i in range(n):
        for j in range(m):
            v = a[i][j]
            if i + 1 < n:
                v ^= a[i + 1][j]
            if j + 1 < m:
                v ^= a[i][j + 1]
            if i + 1 < n and j + 1 < m:
                v ^= a[i + 1][j + 1]

            e[i][j] = v
            weight += v

    ans = weight

    if e[n - 1][m - 1] == 1 and n > 1 and m > 1:
        found = False
        last_row = e[n - 1]

        for i in range(n - 1):
            if e[i][m - 1] == 0:
                continue

            row_i = e[i]
            for j in range(m - 1):
                if row_i[j] and last_row[j]:
                    found = True
                    break

            if found:
                break

        if found:
            ans -= 1

    print(ans)


if __name__ == "__main__":
    main()