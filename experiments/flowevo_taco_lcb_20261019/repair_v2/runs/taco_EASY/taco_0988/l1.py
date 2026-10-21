import sys
from collections import deque


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    ax, ay, bx, by, cx, cy = data[1:7]

    ax -= 1
    ay -= 1
    bx -= 1
    by -= 1
    cx -= 1
    cy -= 1

    state = bytearray(n * n)

    # Mark queen's row
    row_start = ax * n
    for y in range(n):
        state[row_start + y] = 1

    # Mark queen's column
    for x in range(n):
        state[x * n + ay] = 1

    # Mark queen's diagonals
    for x in range(n):
        y = x - ax + ay
        if 0 <= y < n:
            state[x * n + y] = 1

        y = ax + ay - x
        if 0 <= y < n:
            state[x * n + y] = 1

    start = bx * n + by
    target = cx * n + cy

    if start == target:
        print("YES")
        return

    if state[start] or state[target]:
        print("NO")
        return

    state[start] = 1
    queue = deque([start])

    directions = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    )

    while queue:
        current = queue.popleft()

        if current == target:
            print("YES")
            return

        x, y = divmod(current, n)

        for dx, dy in directions:
            nx = x + dx
            ny = y + dy

            if 0 <= nx < n and 0 <= ny < n:
                nxt = nx * n + ny
                if state[nxt] == 0:
                    state[nxt] = 1
                    queue.append(nxt)

    print("NO")


if __name__ == "__main__":
    main()