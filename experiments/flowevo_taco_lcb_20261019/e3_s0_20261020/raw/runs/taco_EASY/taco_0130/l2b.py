import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a1 = data[idx]
        idx += 1

        min_other = 10**18
        for _ in range(n - 1):
            value = data[idx]
            idx += 1
            if value < min_other:
                min_other = value

        if a1 > min_other:
            answers.append("Alice")
        else:
            answers.append("Bob")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()