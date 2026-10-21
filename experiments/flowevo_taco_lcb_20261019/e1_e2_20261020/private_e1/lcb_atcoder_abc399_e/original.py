```python
import sys


def main() -> None:
    input = sys.stdin.readline

    N = int(input())
    S = input().strip()
    T = input().strip()

    g = [-1] * 26

    for a, b in zip(S, T):
        u = ord(a) - ord('a')
        v = ord(b) - ord('a')

        if g[u] == -1:
            g[u] = v
        elif g[u] != v:
            print(-1)
            return