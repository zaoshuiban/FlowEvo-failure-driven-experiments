import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        used = [False] * (n + 1)
        possible = True

        for value in a:
            x = value

            while x > n:
                x //= 2

            while x > 0 and used[x]:
                x //= 2

            if x == 0:
                possible = False
            else:
                used[x] = True

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()