import sys

def main():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        s = data[idx + 2]
        idx += 3

        if b'*' * k in s:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()