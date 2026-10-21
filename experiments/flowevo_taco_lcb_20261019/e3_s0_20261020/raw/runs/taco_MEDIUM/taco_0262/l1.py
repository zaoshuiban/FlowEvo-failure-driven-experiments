def who_is_winner(pieces_position_list):
    board = [[None] * 7 for _ in range(6)]
    heights = [0] * 7

    def is_winning_move(row, col, color):
        directions = ((1, 0), (0, 1), (1, 1), (1, -1))

        for dr, dc in directions:
            count = 1

            for step in (1, -1):
                r = row + dr * step
                c = col + dc * step

                while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == color:
                    count += 1
                    r += dr * step
                    c += dc * step

            if count >= 4:
                return True

        return False

    for move in pieces_position_list:
        column, color = move.split("_")
        col = ord(column) - ord("A")
        row = 5 - heights[col]

        board[row][col] = color
        heights[col] += 1

        if is_winning_move(row, col, color):
            return color

    return "Draw"