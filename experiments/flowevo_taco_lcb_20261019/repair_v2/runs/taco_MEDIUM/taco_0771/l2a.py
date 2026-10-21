import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        permutation = []
        for i in range(n):
            if i % 2 == 0:
                permutation.append(n - i // 2)
            else:
                permutation.append(i // 2 + 1)

        answers.append(" ".join(map(str, permutation)))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()