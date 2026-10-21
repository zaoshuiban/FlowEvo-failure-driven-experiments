import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        s = data[idx + 2]
        idx += 3

        operations = 0
        i = 0

        while i < n:
            if s[i] == ord('B'):
                operations += 1
                i += k
            else:
                i += 1

        answers.append(str(operations))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()