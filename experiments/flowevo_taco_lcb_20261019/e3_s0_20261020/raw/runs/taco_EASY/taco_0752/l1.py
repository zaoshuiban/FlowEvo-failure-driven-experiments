import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    answers = []

    for x in data[1:1 + t]:
        r = x % 14
        if x >= 15 and 1 <= r <= 6:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()