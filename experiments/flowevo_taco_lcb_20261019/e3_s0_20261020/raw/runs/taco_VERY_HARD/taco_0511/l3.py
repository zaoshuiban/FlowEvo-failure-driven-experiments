import sys


def solve() -> None:
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

        # Find the position of the maximum-valued disc.
        max_pos = 1
        max_val = -1

        for i in range(n):
            val = data[idx + i]
            if val > max_val:
                max_val = val
                max_pos = i + 1  # 1-based position

        idx += n

        moves = data[idx:idx + k]
        idx += k
        moves.sort()

        # Number of discs below the maximum-valued disc.
        suffix = n - max_pos

        # win[d] is True if the player to move can force taking the maximum disc
        # when it is at position d from the top (1-based).
        win = bytearray(max_pos + 1)

        for d in range(1, max_pos + 1):
            can_win = 0
            limit = d + suffix

            for x in moves:
                if x < d:
                    if win[d - x] == 0:
                        can_win = 1
                        break
                else:
                    if x <= limit:
                        can_win = 1
                    break

            win[d] = can_win

        if win[max_pos]:
            answers.append("Chef")
        else:
            answers.append("Garry")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()