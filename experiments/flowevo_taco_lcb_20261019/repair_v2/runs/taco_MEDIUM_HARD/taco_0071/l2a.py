import sys

def solve():
    board = ''.join(sys.stdin.read().split())

    x_count = board.count('X')
    o_count = board.count('0')

    winning_lines = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    )

    def has_won(player):
        return any(
            board[a] == board[b] == board[c] == player
            for a, b, c in winning_lines
        )

    x_won = has_won('X')
    o_won = has_won('0')

    if x_won and o_won:
        verdict = "illegal"
    elif x_won:
        verdict = "the first player won" if x_count == o_count + 1 else "illegal"
    elif o_won:
        verdict = "the second player won" if x_count == o_count else "illegal"
    else:
        if x_count == o_count:
            verdict = "draw" if x_count + o_count == 9 else "first"
        elif x_count == o_count + 1:
            verdict = "draw" if x_count + o_count == 9 else "second"
        else:
            verdict = "illegal"

    print(verdict)


if __name__ == "__main__":
    solve()