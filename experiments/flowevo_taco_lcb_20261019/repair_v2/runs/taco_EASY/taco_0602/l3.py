import sys
from collections import deque


def min_moves(n, cells):
    start = end = -1
    for i in range(n):
        for j in range(n):
            ch = cells[i * n + j]
            if ch == 'S':
                start = i * n + j
            elif ch == 'E':
                end = i * n + j

    if start == -1 or end == -1:
        return -1

    dist = [-1] * (n * n)
    dist[start] = 0
    q = deque([start])

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while q:
        pos = q.popleft()

        if pos == end:
            return dist[pos]

        r, c = divmod(pos, n)

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if 0 <= nr < n and 0 <= nc < n:
                npos = nr * n + nc
                if cells[npos] != 'T' and dist[npos] == -1:
                    dist[npos] = dist[pos] + 1
                    q.append(npos)

    return -1


def main():
    tokens = sys.stdin.read().split()
    if not tokens:
        return

    idx = 0
    total_tokens = len(tokens)
    answers = []

    # Process one or more test cases until EOF.
    while idx < total_tokens:
        try:
            n = int(tokens[idx])
        except ValueError:
            break

        idx += 1

        if n <= 0:
            break

        needed = n * n
        chars = []
        length = 0

        while idx < total_tokens and length < needed:
            token = tokens[idx]
            chars.append(token)
            length += len(token)
            idx += 1

        cells = ''.join(chars)
        if len(cells) < needed:
            break

        cells = cells[:needed]
        answers.append(str(min_moves(n, cells)))

    sys.stdout.write('\n'.join(answers))


if __name__ == "__main__":
    main()