import sys

def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        idx += 1
        starter = data[idx]
        idx += 1

        total_value = 0

        for _ in range(n):
            s = data[idx]
            idx += 1

            max_suffix = 0
            min_suffix = 0
            value = 0

            for ch in reversed(s):
                if ch == ord('0'):
                    value = max_suffix + 1
                else:
                    value = min_suffix - 1

                if value > max_suffix:
                    max_suffix = value
                if value < min_suffix:
                    min_suffix = value

            total_value += value

        if total_value > 0:
            answers.append("Dee")
        elif total_value < 0:
            answers.append("Dum")
        else:
            if starter == b"Dee":
                answers.append("Dum")
            else:
                answers.append("Dee")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()