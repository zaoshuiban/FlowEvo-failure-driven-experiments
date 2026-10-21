import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)

        arr = [next(it) for _ in range(n)]
        values = set(arr)

        possible = False
        for x in arr:
            if x + k in values:
                possible = True
                break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()