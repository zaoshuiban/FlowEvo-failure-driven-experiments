import sys


def main():
    input = sys.stdin.readline

    n, m = map(int, input().split())
    INF = 10**9

    # costs[i][0] = min moves to make row i a digit
    # costs[i][1] = min moves to make row i a lowercase letter
    # costs[i][2] = min moves to make row i one of '#', '*', '&'
    costs = [[INF, INF, INF] for _ in range(n)]

    for i in range(n):
        s = input().strip()

        for pos, ch in enumerate(s):
            if '0' <= ch <= '9':
                t = 0
            elif 'a' <= ch <= 'z':
                t = 1
            elif ch in '#*&':
                t = 2
            else:
                continue

            dist = min(pos, m - pos)
            if dist < costs[i][t]:
                costs[i][t] = dist

    answer = INF

    # Choose three distinct rows for digit, lowercase letter, and special symbol.
    for digit_row in range(n):
        if costs[digit_row][0] == INF:
            continue

        for letter_row in range(n):
            if letter_row == digit_row or costs[letter_row][1] == INF:
                continue

            for special_row in range(n):
                if special_row == digit_row or special_row == letter_row:
                    continue
                if costs[special_row][2] == INF:
                    continue

                total = (
                    costs[digit_row][0]
                    + costs[letter_row][1]
                    + costs[special_row][2]
                )
                answer = min(answer, total)

    print(answer)


if __name__ == "__main__":
    main()