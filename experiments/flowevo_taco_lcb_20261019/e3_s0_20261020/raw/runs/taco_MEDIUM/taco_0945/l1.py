import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        rankings = [[next(it) for _ in range(5)] for _ in range(n)]

        candidate = 0

        for i in range(1, n):
            better = 0
            for j in range(5):
                if rankings[i][j] < rankings[candidate][j]:
                    better += 1
            if better >= 3:
                candidate = i

        valid = True
        for i in range(n):
            if i == candidate:
                continue
            better = 0
            for j in range(5):
                if rankings[candidate][j] < rankings[i][j]:
                    better += 1
            if better < 3:
                valid = False
                break

        answers.append(str(candidate + 1 if valid else -1))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()