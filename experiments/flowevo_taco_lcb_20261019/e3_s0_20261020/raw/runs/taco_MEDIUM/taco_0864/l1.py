import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        arr = data[idx:idx + n]
        idx += n

        if n == 1:
            answers.append("YES")
        else:
            if min(arr) + max(arr) <= k:
                answers.append("YES")
            else:
                answers.append("NO")

    print("\n".join(answers))

if __name__ == "__main__":
    solve()