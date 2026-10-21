import sys

LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]


def wins(board, player):
    for a, b, c in LINES:
        if board[a] == board[b] == board[c] == player:
            return True
    return False


def main():
    board = ''.join(sys.stdin.read().split())

    if len(board) != 9:
        print("illegal")
        return

    x_count = board.count('X')
    o_count = board.count('0')

    if x_count < o_count or x_count > o_count + 1:
        print("illegal")
        return

    x_wins = wins(board, 'X')
    o_wins = wins(board, '0')

    if x_wins and o_wins:
        print("illegal")
        return

    if x_wins:
        if x_count != o_count + 1:
            print("illegal")
            return

        possible = False
        for i, ch in enumerate(board):
            if ch == 'X':
                new_board = board[:i] + '.' + board[i + 1:]
                if not wins(new_board, 'X'):
                    possible = True
                    break

        print("the first player won" if possible else "illegal")
        return

    if o_wins:
        if x_count != o_count:
            print("illegal")
            return

        possible = False
        for i, ch in enumerate(board):
            if ch == '0':
                new_board = board[:i] + '.' + board[i + 1:]
                if not wins(new_board, '0'):
                    possible = True
                    break

        print("the second player won" if possible else "illegal")
        return

    if '.' not in board:
        print("draw")
    else:
        print("first" if x_count == o_count else "second")


if __name__ == "__main__":
    main()