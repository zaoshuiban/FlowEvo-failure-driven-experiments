import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        freq = [0] * (n + 2)

        for _ in range(n):
            x = data[idx]
            idx += 1

            while x > n:
                x //= 2

            freq[x] += 1

        for value in range(n, 1, -1):
            while freq[value] > 1:
                freq[value] -= 1
                freq[value // 2] += 1

        if all(freq[i] == 1 for i in range(1, n + 1)):
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()