import sys
from collections import deque


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    n = int(next(it))
    m = int(next(it))

    pos = [0] * (m + 1)
    hp = [0] * (m + 1)

    for i in range(1, m + 1):
        pos[i] = int(next(it))
        hp[i] = int(next(it))

    a = [0] + [int(next(it)) for _ in range(n)]

    # reqL[l][r] = minimum HP needed to traverse cells l, l+1, ..., r
    reqL = [[0] * (n + 2) for _ in range(n + 2)]

    for l in range(1, n + 1):
        cur = 0
        min_pref = 0
        for r in range(l, n + 1):
            cur += a[r]
            if cur < min_pref:
                min_pref = cur
            reqL[l][r] = -min_pref

    # reqR[l][r] = minimum HP needed to traverse cells r, r-1, ..., l
    reqR = [[0] * (n + 2) for _ in range(n + 2)]

    for l in range(1, n + 1):
        for r in range(l, n + 1):
            cur = 0
            min_pref = 0
            for idx in range(r, l - 1, -1):
                cur += a[idx]
                if cur < min_pref:
                    min_pref = cur
            reqR[l][r] = -min_pref

    for rally in range(1, n + 1):
        left_min = rally
        right_max = rally

        for i in range(1, m + 1):
            s = pos[i]
            if s < rally:
                if s < left_min:
                    left_min = s
            elif s > rally:
                if s > right_max:
                    right_max = s

        # If the rally cell is blank, the cell is already harmless.
        initial_cleared = (a[rally] == 0)

        start = (rally, rally, initial_cleared)
        q = deque([start])
        prev = {start: (None, None)}

        final_state = None

        while q:
            L, R, cleared = q.popleft()

            if L == left_min and R == right_max and cleared:
                final_state = (L, R, cleared)
                break

            for i in range(1, m + 1):
                s = pos[i]

                if s < L:
                    lcell = s + 1
                    rcell = L

                    if cleared and rcell == rally:
                        if lcell <= rally - 1:
                            req = reqL[lcell][rally - 1]
                        else:
                            req = 0
                    else:
                        req = reqL[lcell][rcell]

                    if hp[i] >= req:
                        nxt = (s, R, True)
                        if nxt not in prev:
                            prev[nxt] = ((L, R, cleared), i)
                            q.append(nxt)

                elif s > R:
                    lcell = R
                    rcell = s - 1

                    if cleared and lcell == rally:
                        if rally + 1 <= rcell:
                            req = reqR[rally + 1][rcell]
                        else:
                            req = 0
                    else:
                        req = reqR[lcell][rcell]

                    if hp[i] >= req:
                        nxt = (L, s, True)
                        if nxt not in prev:
                            prev[nxt] = ((L, R, cleared), i)
                            q.append(nxt)

        if final_state is None:
            continue

        order_records = []
        state = final_state

        while True:
            prev_state, hero_idx = prev[state]
            if prev_state is None:
                break
            order_records.append(hero_idx)
            state = prev_state

        order_records.reverse()

        used = [False] * (m + 1)
        for idx in order_records:
            used[idx] = True

        answer_order = order_records[:]
        for i in range(1, m + 1):
            if not used[i]:
                answer_order.append(i)

        sys.stdout.write(str(rally) + "\n")
        sys.stdout.write(" ".join(map(str, answer_order)) + "\n")
        return

    sys.stdout.write("-1\n")


if __name__ == "__main__":
    solve()