import sys

LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]

WIN_VERDICT = {
    'X': "the first player won",
    '0': "the second player won"
}

verdict = {}


def get_winner(board):
    for a, b, c in LINES:
        if board[a] != '.' and board[a] == board[b] == board[c]:
            return board[a]
    return None


def dfs(board, turn):
    if board in verdict:
        return

    winner = get_winner(board)

    if winner is not None:
        verdict[board] = WIN_VERDICT[winner]
        return

    if '.' not in board:
        verdict[board] = "draw"
        return

    verdict[board] = "first" if turn == 'X' else "second"

    next_turn = '0' if turn == 'X' else 'X'

    for i, ch in enumerate(board):
        if ch == '.':
            new_board = board[:i] + turn + board[i + 1:]
            dfs(new_board, next_turn)


def main():
    dfs('.' * 9, 'X')

    board = ''.join(sys.stdin.read().split())
    board = board.replace('O', '0')

    print(verdict.get(board, "illegal"))


if __name__ == "__main__":
    main()