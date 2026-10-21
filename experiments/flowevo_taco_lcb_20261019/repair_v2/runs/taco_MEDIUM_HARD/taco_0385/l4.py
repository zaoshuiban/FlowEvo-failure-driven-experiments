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

        total = 0

        for _ in range(n):
            s = data[idx]
            idx += 1

            # Values of all suffixes processed so far.
            # Start with the empty suffix, whose value is 0.
            max_suf = 0
            min_suf = 0
            cur = 0

            for ch in reversed(s):
                if ch == ord('0'):
                    cur = max_suf + 1
                else:
                    cur = min_suf - 1

                if cur > max_suf:
                    max_suf = cur
                if cur < min_suf:
                    min_suf = cur

            total += cur

        if total > 0:
            answers.append("Dee")
        elif total < 0:
            answers.append("Dum")
        else:
            # A zero game is won by the second player.
            answers.append("Dum" if starter == b"Dee" else "Dee")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()