import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []
    STAR = ord('*')  # 42, since iterating over bytes gives integers

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        s = data[idx + 2]
        idx += 3

        consecutive = 0
        found = False

        for ch in s:
            if ch == STAR:
                consecutive += 1
                if consecutive >= k:
                    found = True
                    break
            else:
                consecutive = 0

        answers.append("YES" if found else "NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()