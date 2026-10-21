import sys


def build_trans(blocked):
    res = [0] * 4
    for pre in range(4):
        if pre & blocked:
            continue

        occupied = pre | blocked
        available = 3 ^ occupied
        possible_next = 0

        def dfs(avail, nxt):
            nonlocal possible_next
            if avail == 0:
                possible_next |= 1 << nxt
                return

            p = avail & -avail

            # Put a horizontal domino going to the next column
            dfs(avail ^ p, nxt | p)

            # Put a vertical domino inside the current column
            other = p ^ 3
            if avail & other:
                dfs(avail ^ p ^ other, nxt)

        dfs(available, 0)
        res[pre] = possible_next

    return res


trans_by_blocked = [build_trans(b) for b in range(4)]

MAXK = 31
pow_rel = [trans_by_blocked[0]]

for _ in range(1, MAXK):
    prev = pow_rel[-1]
    cur = [0] * 4

    for i in range(4):
        bits = prev[i]
        val = 0

        if bits & 1:
            val |= prev[0]
        if bits & 2:
            val |= prev[1]
        if bits & 4:
            val |= prev[2]
        if bits & 8:
            val |= prev[3]

        cur[i] = val

    pow_rel.append(cur)


def apply_gap(states, length):
    k = 0

    while length:
        if length & 1:
            rel = pow_rel[k]
            new_states = 0

            if states & 1:
                new_states |= rel[0]
            if states & 2:
                new_states |= rel[1]
            if states & 4:
                new_states |= rel[2]
            if states & 8:
                new_states |= rel[3]

            states = new_states

        length >>= 1
        k += 1

    return states


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        cells = []

        for _ in range(m):
            r = next(it)
            c = next(it)
            cells.append((c, 1 << (r - 1)))

        cells.sort()

        events = []
        idx = 0

        while idx < m:
            c = cells[idx][0]
            blocked = 0

            while idx < m and cells[idx][0] == c:
                blocked |= cells[idx][1]
                idx += 1

            events.append((c, blocked))

        states = 1
        prev_col = 0

        for c, blocked in events:
            states = apply_gap(states, c - prev_col - 1)

            trans = trans_by_blocked[blocked]
            new_states = 0

            if states & 1:
                new_states |= trans[0]
            if states & 2:
                new_states |= trans[1]
            if states & 4:
                new_states |= trans[2]
            if states & 8:
                new_states |= trans[3]

            states = new_states
            prev_col = c

        states = apply_gap(states, n - prev_col)

        answers.append("YES" if states & 1 else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()