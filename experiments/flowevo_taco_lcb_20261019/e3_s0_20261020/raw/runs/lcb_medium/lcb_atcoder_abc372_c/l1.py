import sys

def is_abc(s, i):
    return s[i] == 65 and s[i + 1] == 66 and s[i + 2] == 67  # 'A', 'B', 'C'

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    q = int(data[1])
    s = bytearray(data[2])

    count = 0
    for i in range(n - 2):
        if is_abc(s, i):
            count += 1

    answers = []
    idx = 3

    for _ in range(q):
        p = int(data[idx]) - 1
        c = data[idx + 1][0]
        idx += 2

        left = max(0, p - 2)
        right = min(n - 3, p)

        for i in range(left, right + 1):
            if is_abc(s, i):
                count -= 1

        s[p] = c

        for i in range(left, right + 1):
            if is_abc(s, i):
                count += 1

        answers.append(str(count))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()