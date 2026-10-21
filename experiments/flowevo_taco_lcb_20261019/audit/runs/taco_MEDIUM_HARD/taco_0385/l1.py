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
        starter = data[idx + 1]
        idx += 2

        total_value = 0

        for _ in range(n):
            s = data[idx]
            idx += 1

            max_later = 0
            min_later = 0
            value = 0

            for ch in reversed(s):
                if ch == '0':
                    value = max_later + 1
                else:
                    value = min_later - 1

                if value > max_later:
                    max_later = value
                if value < min_later:
                    min_later = value

            total_value += value

        if total_value > 0:
            answers.append("Dee")
        elif total_value < 0:
            answers.append("Dum")
        else:
            answers.append("Dum" if starter == "Dee" else "Dee")

    print("\n".join(answers))


if __name__ == "__main__":
    solve()