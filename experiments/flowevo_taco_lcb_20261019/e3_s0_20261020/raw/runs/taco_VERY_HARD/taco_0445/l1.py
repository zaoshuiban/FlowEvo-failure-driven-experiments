import sys
from collections import deque


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    idx = 0
    t = int(data[idx])
    idx += 1

    answers = []

    for _ in range(t):
        n = int(data[idx])
        idx += 1

        a = list(map(int, data[idx:idx + n]))
        idx += n

        s = data[idx]
        idx += 1

        # Components formed by consecutive '=' relations.
        comp = [0] * n
        fixed = [-1] * n

        m = 1
        if a[0] != -1:
            fixed[0] = a[0]

        valid = True

        for i in range(1, n):
            if s[i - 1] == ord('='):
                c = comp[i - 1]
                comp[i] = c

                if a[i] != -1:
                    if fixed[c] == -1:
                        fixed[c] = a[i]
                    elif fixed[c] != a[i]:
                        valid = False
            else:
                comp[i] = m

                if a[i] != -1:
                    fixed[m] = a[i]

                m += 1

        if not valid:
            answers.append("NO")
            continue

        # For each boundary between components:
        # dirs[c] = 1  means edge c -> c + 1 ('<')
        # dirs[c] = -1 means edge c + 1 -> c ('>')
        dirs = [0] * (m - 1)

        for i in range(n - 1):
            ch = s[i]
            if ch == ord('='):
                continue

            c = comp[i]

            if ch == ord('<'):
                dirs[c] = 1
            else:
                dirs[c] = -1

        indeg = [0] * m

        for c in range(m - 1):
            if dirs[c] == 1:
                indeg[c + 1] += 1
            elif dirs[c] == -1:
                indeg[c] += 1

        lower = [0] * m

        for c in range(m):
            if fixed[c] > lower[c]:
                lower[c] = fixed[c]

        q = deque()

        for c in range(m):
            if indeg[c] == 0:
                q.append(c)

        processed = 0

        while q:
            u = q.popleft()
            processed += 1

            if u < m - 1 and dirs[u] == 1:
                v = u + 1
                required = lower[u] + 1

                if lower[v] < required:
                    lower[v] = required

                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)

            if u > 0 and dirs[u - 1] == -1:
                v = u - 1
                required = lower[u] + 1

                if lower[v] < required:
                    lower[v] = required

                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)

        if processed != m:
            valid = False

        if valid:
            for c in range(m):
                if fixed[c] != -1 and lower[c] > fixed[c]:
                    valid = False
                    break

        answers.append("YES" if valid else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()