import sys
from collections import deque


def minimum_moves(n, cells):
    total = n * n
    start = end = -1

    for i in range(min(total, len(cells))):
        if cells[i] == 'S':
            start = i
        elif cells[i] == 'E':
            end = i

    if start == -1 or end == -1:
        return -1

    dist = [-1] * total
    dist[start] = 0
    q = deque([start])

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while q:
        pos = q.popleft()

        if pos == end:
            return dist[pos]

        r, c = divmod(pos, n)

        for dr, dc in directions:
            nr = r + dr
            nc = c + dc

            if 0 <= nr < n and 0 <= nc < n:
                npos = nr * n + nc

                if cells[npos] != 'T' and dist[npos] == -1:
                    dist[npos] = dist[pos] + 1
                    q.append(npos)

    return -1


def main():
    tokens = sys.stdin.buffer.read().split()
    if not tokens:
        return

    answers = []
    idx = 0

    # Detect whether the first number is a test-case count or the grid size N.
    use_test_cases = False
    if len(tokens) >= 2:
        try:
            int(tokens[0])
            int(tokens[1])
            use_test_cases = True
        except ValueError:
            use_test_cases = False

    if use_test_cases:
        test_cases = int(tokens[0])
        idx = 1

        for _ in range(test_cases):
            if idx >= len(tokens):
                break

            n = int(tokens[idx])
            idx += 1

            need = n * n
            parts = []
            count = 0

            while idx < len(tokens) and count < need:
                part = tokens[idx].decode()
                parts.append(part)
                count += len(part)
                idx += 1

            if count < need:
                break

            cells = ''.join(parts)
            if len(cells) > need:
                cells = cells[:need]

            answers.append(str(minimum_moves(n, cells)))

    else:
        while idx < len(tokens):
            try:
                n = int(tokens[idx])
            except ValueError:
                break

            idx += 1

            if n <= 0:
                break

            need = n * n
            parts = []
            count = 0

            while idx < len(tokens) and count < need:
                part = tokens[idx].decode()
                parts.append(part)
                count += len(part)
                idx += 1

            if count < need:
                break

            cells = ''.join(parts)
            if len(cells) > need:
                cells = cells[:need]

            answers.append(str(minimum_moves(n, cells)))

    sys.stdout.write('\n'.join(answers))
    if answers:
        sys.stdout.write('\n')


if __name__ == "__main__":
    main()