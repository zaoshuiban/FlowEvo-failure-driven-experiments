import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        m = int(next(it))
        strings = [next(it) for _ in range(n)]

        base = strings[0]
        candidates = {base}

        for pos in range(m):
            for c in "abcdefghijklmnopqrstuvwxyz":
                if c != base[pos]:
                    candidates.add(base[:pos] + c + base[pos + 1:])

        answer = None

        for candidate in candidates:
            valid = True

            for s in strings:
                diff = 0
                for j in range(m):
                    if s[j] != candidate[j]:
                        diff += 1
                        if diff > 1:
                            break

                if diff > 1:
                    valid = False
                    break

            if valid:
                answer = candidate
                break

        answers.append(answer if answer is not None else "-1")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()