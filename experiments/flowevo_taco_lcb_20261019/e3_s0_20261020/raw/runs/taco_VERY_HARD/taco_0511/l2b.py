import sys

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        s = data[idx:idx + k]
        idx += k

        # Position of the maximum value, 1-based.
        max_pos = 1
        max_val = a[0]
        for i in range(1, n):
            if a[i] > max_val:
                max_val = a[i]
                max_pos = i + 1

        # Number of discs after the maximum-valued disc.
        suffix = n - max_pos

        s.sort()

        # win[d] = whether the player to move can force taking the maximum disc
        # when it is d positions away (including itself) from the top.
        win = [False] * (max_pos + 1)

        for d in range(1, max_pos + 1):
            can_win = False

            for x in s:
                if x < d:
                    # Do not take the maximum yet; opponent moves next.
                    if not win[d - x]:
                        can_win = True
                        break
                elif x <= d + suffix:
                    # This move takes the maximum-valued disc.
                    can_win = True
                    break
                else:
                    # Since s is sorted, all larger moves are invalid.
                    break

            win[d] = can_win

        answers.append("Chef" if win[max_pos] else "Garry")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()