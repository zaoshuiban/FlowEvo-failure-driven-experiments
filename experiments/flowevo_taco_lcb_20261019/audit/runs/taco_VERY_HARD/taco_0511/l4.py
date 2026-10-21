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

        max_pos = 1
        max_val = -1

        # Find the position of the unique maximum-valued disc.
        for i in range(1, n + 1):
            value = data[idx]
            idx += 1
            if value > max_val:
                max_val = value
                max_pos = i

        moves = data[idx:idx + k]
        idx += k
        moves.sort()

        # Number of discs below the maximum-valued disc.
        below = n - max_pos

        # win[d] = whether the player to move can force taking the maximum disc
        # when there are d discs remaining up to and including it.
        win = [0] * (max_pos + 1)

        for d in range(1, max_pos + 1):
            limit = d + below
            can_win = 0

            for x in moves:
                if x < d:
                    if win[d - x] == 0:
                        can_win = 1
                        break
                else:
                    # The maximum disc is taken in this move iff x <= limit.
                    if x <= limit:
                        can_win = 1
                    break

            win[d] = can_win

        # The unique maximum disc decides the winner.
        answers.append("Chef" if win[max_pos] else "Garry")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()