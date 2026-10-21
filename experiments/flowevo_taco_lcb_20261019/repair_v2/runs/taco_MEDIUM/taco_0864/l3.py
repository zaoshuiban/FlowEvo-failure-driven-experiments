import sys

def solve():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        k = int(next(it))

        arr = [int(next(it)) for _ in range(n)]

        if n == 1:
            answers.append("YES")
        else:
            if min(arr) + max(arr) <= k:
                answers.append("YES")
            else:
                answers.append("NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()