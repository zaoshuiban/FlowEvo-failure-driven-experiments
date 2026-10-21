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

        a = data[idx:idx + n]
        idx += n

        if k not in a:
            answers.append("no")
            continue

        if n == 1:
            answers.append("yes" if a[0] == k else "no")
            continue

        possible = False

        for i in range(n):
            if a[i] >= k:
                if i + 1 < n and a[i + 1] >= k:
                    possible = True
                    break
                if i + 2 < n and a[i + 2] >= k:
                    possible = True
                    break

        answers.append("yes" if possible else "no")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()