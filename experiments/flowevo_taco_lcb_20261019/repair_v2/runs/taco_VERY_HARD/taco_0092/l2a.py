import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [0] * n
    b = [0] * n

    p = 1
    for i in range(n):
        a[i] = data[p] - 1
        b[i] = data[p + 1] - 1
        p += 2

    # All multisets of destination floors, with at most 4 passengers inside.
    counts = []
    idmap = {}
    arr = [0] * 9

    def gen(pos: int, left: int) -> None:
        if pos == 9:
            t = tuple(arr)
            idmap[t] = len(counts)
            counts.append(t)
            return
        for c in range(left + 1):
            arr[pos] = c
            gen(pos + 1, left - c)

    gen(0, 4)

    m_states = len(counts)
    size = [sum(t) for t in counts]

    rem = [[0] * 9 for _ in range(m_states)]
    add = [[-1] * 9 for _ in range(m_states)]
    drop_options = [None] * m_states

    for state, t in enumerate(counts):
        drops = []
        for floor in range(9):
            if t[floor] > 0:
                new_counts = list(t)
                new_counts[floor] = 0
                new_id = idmap[tuple(new_counts)]
                rem[state][floor] = new_id
                drops.append((floor, new_id))
            else:
                rem[state][floor] = state
        drop_options[state] = drops

        if size[state] < 4:
            for floor in range(9):
                new_counts = list(t)
                new_counts[floor] += 1
                add[state][floor] = idmap[tuple(new_counts)]

    empty_state = idmap[tuple([0] * 9)]
    order = sorted(range(m_states), key=lambda x: size[x], reverse=True)

    # Number of consecutive next employees with the same starting floor, capped at 4.
    run_cap = [1] * n
    for i in range(n - 2, -1, -1):
        if a[i] == a[i + 1]:
            run_cap[i] = min(4, run_cap[i + 1] + 1)
        else:
            run_cap[i] = 1

    L = m_states * 9
    INF = 10 ** 8
    INF_ROW = [INF] * L

    # bufs[k % 5] stores initial distances for having boarded exactly k people.
    bufs = [[INF] * L for _ in range(5)]
    bufs[0][empty_state * 9 + 0] = 0  # Initially floor 1 (index 0)

    answer = INF

    for k in range(n + 1):
        slot = bufs[k % 5]

        # Deliver any number of currently inside passengers before boarding anyone new.
        for state in order:
            drops = drop_options[state]
            if not drops:
                continue

            base = state * 9
            for floor in range(9):
                val = slot[base + floor]
                if val >= INF:
                    continue

                for dest, new_state in drops:
                    move = floor - dest
                    if move < 0:
                        move = -move
                    new_val = val + move
                    idx = new_state * 9 + dest
                    if new_val < slot[idx]:
                        slot[idx] = new_val

        if k == n:
            base = empty_state * 9
            answer = min(slot[base + floor] for floor in range(9))
            break

        origin = a[k]
        run_len = run_cap[k]

        # Board the next employees, possibly after some passengers got out at this floor.
        for state in range(m_states):
            after_exit = rem[state][origin]
            free_space = 4 - size[after_exit]
            if free_space <= 0:
                continue

            board_count = free_space if free_space < run_len else run_len
            new_state = after_exit
            end_k = k + board_count

            for t in range(k, end_k):
                new_state = add[new_state][b[t]]

            target = bufs[end_k % 5]
            base = state * 9
            target_idx = new_state * 9 + origin

            for floor in range(9):
                val = slot[base + floor]
                if val >= INF:
                    continue

                move = floor - origin
                if move < 0:
                    move = -move

                new_val = val + move
                if new_val < target[target_idx]:
                    target[target_idx] = new_val

        slot[:] = INF_ROW

    # Every employee enters once and exits once: exactly 2 seconds per employee.
    print(answer + 2 * n)


if __name__ == "__main__":
    solve()