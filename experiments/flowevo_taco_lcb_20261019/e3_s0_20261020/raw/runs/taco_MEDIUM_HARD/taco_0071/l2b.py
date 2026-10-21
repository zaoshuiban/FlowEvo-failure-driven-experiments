import sys

def get_winner(board):
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in lines:
        if board[a] != '.' and board[a] == board[b] == board[c]:
            return board[a]
    return None

verdict = {}
seen = set()

def dfs(board, turn):
    if board in seen:
        return
    seen.add(board)

    w = get_winner(board)

    if w == 'X':
        verdict[board] = "the first player won"
        return
    if w == '0':
        verdict[board] = "the second player won"
        return

    if '.' not in board:
        verdict[board] = "draw"
        return

    verdict[board] = "first" if turn == 'X' else "second"

    for i, ch in enumerate(board):
        if ch == '.':
            new_board = board[:i] + turn + board[i + 1:]
            dfs(new_board, '0' if turn == 'X' else 'X')

dfs('.' * 9, 'X')

board = ''.join(sys.stdin.read().split())
print(verdict.get(board, "illegal"))