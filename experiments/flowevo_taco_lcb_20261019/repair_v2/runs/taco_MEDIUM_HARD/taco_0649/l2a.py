import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []
    alphabet = "abcdefghijklmnopqrstuvwxyz"

    for _ in range(t):
        n = int(next(it))
        m = int(next(it))
        strings = [next(it) for _ in range(n)]

        base = strings[0]
        candidates = [base]

        for i in range(m):
            for c in alphabet:
                if c != base[i]:
                    candidates.append(base[:i] + c + base[i + 1:])

        answer = None

        for candidate in candidates:
            valid = True

            for s in strings:
                diff = 0
                for x, y in zip(candidate, s):
                    if x != y:
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

    print("\n".join(answers))


if __name__ == "__main__":
    solve()