import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        strings = data[idx:idx + n]
        idx += n

        base = strings[0]
        answer = None

        # Try all strings within Hamming distance at most 1 from the first string.
        # The specific order below matches the sample outputs, but any valid answer is fine.
        for pos in range(m - 1, -1, -1):
            for code in range(25, -1, -1):
                ch = chr(ord('a') + code)
                candidate = base[:pos] + ch + base[pos + 1:]

                valid = True
                for s in strings:
                    diff = 0
                    for i in range(m):
                        if s[i] != candidate[i]:
                            diff += 1
                            if diff > 1:
                                break
                    if diff > 1:
                        valid = False
                        break

                if valid:
                    answer = candidate
                    break

            if answer is not None:
                break

        answers.append(answer if answer is not None else "-1")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()