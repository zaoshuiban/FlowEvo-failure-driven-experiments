import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        p = data[idx:idx + n]
        idx += n

        pos = [0] * (n + 1)
        for i, value in enumerate(p, 1):
            pos[value] = i

        ans = n
        start = 1

        for v in range(1, n + 1):
            if v == n or pos[v] > pos[v + 1]:
                cost = max(start - 1, n - v)
                if cost < ans:
                    ans = cost
                start = v + 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()