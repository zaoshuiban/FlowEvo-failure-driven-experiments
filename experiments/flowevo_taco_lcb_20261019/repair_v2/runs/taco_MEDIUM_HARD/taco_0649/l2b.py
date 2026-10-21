import sys

def solve():
    data = sys.stdin.read().split()
    it = iter(data)

    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        m = int(next(it))
        strings = [next(it) for _ in range(n)]

        base = strings[0]
        answer = None

        for pos in range(m):
            for ch_code in range(26):
                ch = chr(ord('a') + ch_code)
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

    print("\n".join(answers))


if __name__ == "__main__":
    solve()