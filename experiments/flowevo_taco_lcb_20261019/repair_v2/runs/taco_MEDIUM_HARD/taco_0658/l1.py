import sys
from functools import lru_cache

def main():
    input = sys.stdin.readline

    n, m = map(int, input().split())
    graph = [[] for _ in range(n)]

    for _ in range(m):
        v, u, c = input().split()
        v = int(v) - 1
        u = int(u) - 1
        char_code = ord(c) - ord('a')
        graph[v].append((u, char_code))

    @lru_cache(None)
    def can_win(v, other, min_char):
        for nxt, ch in graph[v]:
            if ch >= min_char and not can_win(other, nxt, ch):
                return True
        return False

    answer = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append('A' if can_win(i, j, 0) else 'B')
        answer.append(''.join(row))

    sys.stdout.write('\n'.join(answer))


if __name__ == "__main__":
    main()