```python
import sys
from collections import deque


def bfs_order(n, sources):
    seen = bytearray(n)
    q = deque()

    for s in sources:
        if not seen[s]:
            seen[s] = 1
            q.append(s)