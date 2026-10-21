import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        s = data[idx + 2]
        idx += 3

        count = 0
        strong = False

        for ch in s:
            if ch == ord('*'):
                count += 1
                if count >= k:
                    strong = True
                    break
            else:
                count = 0

        answers.append("YES" if strong else "NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()