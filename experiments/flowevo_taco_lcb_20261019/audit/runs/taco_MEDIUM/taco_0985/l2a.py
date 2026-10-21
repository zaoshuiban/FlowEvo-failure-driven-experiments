import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    strings = data[2:2 + n]

    INF = 10**9
    costs = [[INF] * 3 for _ in range(n)]

    for i, s in enumerate(strings):
        for pos, ch in enumerate(s):
            dist = min(pos, m - pos)

            if '0' <= ch <= '9':
                costs[i][0] = min(costs[i][0], dist)
            elif 'a' <= ch <= 'z':
                costs[i][1] = min(costs[i][1], dist)
            elif ch in '#*&':
                costs[i][2] = min(costs[i][2], dist)

    answer = INF

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            for k in range(n):
                if k == i or k == j:
                    continue

                answer = min(
                    answer,
                    costs[i][0] + costs[j][1] + costs[k][2]
                )

    print(answer)


if __name__ == "__main__":
    main()