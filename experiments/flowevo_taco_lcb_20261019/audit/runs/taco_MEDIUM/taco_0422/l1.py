import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        n = data[pos]
        pos += 1

        result = []

        if n % 2 == 1:
            k = n // 2
            for i in range(n):
                for j in range(i + 1, n):
                    if j - i <= k:
                        result.append(1)
                    else:
                        result.append(-1)
        else:
            for i in range(n):
                for j in range(i + 1, n):
                    if i // 2 == j // 2:
                        result.append(0)
                    elif i % 2 == j % 2:
                        result.append(1)
                    else:
                        result.append(-1)

        answers.append(" ".join(map(str, result)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()