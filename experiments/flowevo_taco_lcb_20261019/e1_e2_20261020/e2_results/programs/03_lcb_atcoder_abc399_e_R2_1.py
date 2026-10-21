import sys


def main() -> None:
    input = sys.stdin.readline

    N = int(input())
    S = input().strip()
    T = input().strip()

    mp = [-1] * 26
    present = [False] * 26

    for a, b in zip(S, T):
        u = ord(a) - ord('a')
        v = ord(b) - ord('a')
        present[u] = True

        if mp[u] == -1:
            mp[u] = v
        elif mp[u] != v:
            print(-1)
            return

    present_nodes = [i for i in range(26) if present[i]]

    # Number of letters that must be changed at least once.
    operations = 0
    for u in present_nodes:
        if mp[u] != u:
            operations += 1

    # indeg[v] = number of present source letters that must become v.
    indeg = [0] * 26
    for u in present_nodes:
        v = mp[u]
        if present[v]:
            indeg[v] += 1

    state = [0] * 26
    in_pure_cycle = [False] * 26
    pure_cycles = 0

    for start in present_nodes:
        if state[start] != 0:
            continue

        path = []
        pos = [-1] * 26
        u = start

        while True:
            if not present[u]:
                break

            if state[u] == 0:
                state[u] = 1
                pos[u] = len(path)
                path.append(u)
                u = mp[u]
            else:
                if state[u] == 1 and pos[u] != -1:
                    idx = pos[u]
                    cycle = path[idx:]

                    # Self-loops are already fixed and require no extra operation.
                    if len(cycle) >= 2:
                        pure = True
                        for v in cycle:
                            if indeg[v] != 1:
                                pure = False
                                break

                        if pure:
                            pure_cycles += 1
                            for v in cycle:
                                in_pure_cycle[v] = True
                break

        for v in path:
            state[v] = 2

    has_empty_letter = len(present_nodes) < 26

    # A non-pure non-fixed component can create an empty temporary letter.
    can_create_empty = False
    for u in present_nodes:
        if mp[u] != u and not in_pure_cycle[u]:
            can_create_empty = True
            break

    if pure_cycles > 0 and not has_empty_letter and not can_create_empty:
        print(-1)
        return

    # Each pure cycle needs one extra temporary operation.
    print(operations + pure_cycles)


if __name__ == "__main__":
    main()
