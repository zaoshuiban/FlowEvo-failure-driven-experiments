import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

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
            mn = min(arr)
            mx = max(arr)
            answers.append("YES" if mn + mx <= k else "NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()