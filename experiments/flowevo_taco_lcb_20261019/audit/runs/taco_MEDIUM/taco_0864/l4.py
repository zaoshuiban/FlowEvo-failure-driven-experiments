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

        first = data[idx]
        mn = mx = first
        for i in range(1, n):
            x = data[idx + i]
            if x < mn:
                mn = x
            if x > mx:
                mx = x
        idx += n

        if n == 1 or mn + mx <= k:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()