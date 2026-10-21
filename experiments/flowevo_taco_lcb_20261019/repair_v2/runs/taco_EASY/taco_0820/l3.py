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

        values = set(arr)
        possible = False

        if k == 0:
            possible = len(values) < n
        else:
            target = abs(k)
            for x in values:
                if x - target in values:
                    possible = True
                    break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()