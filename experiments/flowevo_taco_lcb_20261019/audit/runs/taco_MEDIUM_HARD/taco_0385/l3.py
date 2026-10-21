import sys


def main() -> None:
    tokens = sys.stdin.buffer.read().split()
    if not tokens:
        return

    t = int(tokens[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(tokens[idx])
        idx += 1
        starter = tokens[idx]
        idx += 1

        total_value = 0

        for _ in range(n):
            s = tokens[idx]
            idx += 1

            # vals stores values of all proper suffixes processed so far,
            # including the empty suffix with value 0.
            vals = [0]
            value = 0

            for ch in reversed(s):
                if ch == 48:  # '0'
                    value = max(vals) + 1
                else:         # '1'
                    value = min(vals) - 1
                vals.append(value)

            total_value += value

        if total_value > 0:
            answers.append("Dee")
        elif total_value < 0:
            answers.append("Dum")
        else:
            # Zero game: the starting player loses.
            if starter == b"Dee":
                answers.append("Dum")
            else:
                answers.append("Dee")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()