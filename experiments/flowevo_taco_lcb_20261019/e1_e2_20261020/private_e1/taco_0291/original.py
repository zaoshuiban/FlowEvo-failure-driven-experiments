```python
import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        f = data[idx]
        idx += 1

        unprinted = set()
        for _ in range(f):
            unprinted.add(data[idx])
            idx += 1

        torn = data[idx]
        idx += 1

        total_sum = n * (n + 1) // 2
        unprinted_sum = sum(p for p in unprinted if 1 <= p <= n)
        total_printed = total_sum - unprinted_sum

        # Number of physical leaves in a book with n printed sides.
        leaves = (n + 1) // 2

        if leaves == 0:
            expected = 0.0
        else:
            effective_torn = min(max(torn,