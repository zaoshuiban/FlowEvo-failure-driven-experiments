import sys


def main() -> None:
    input = sys.stdin.readline

    N = int(input())
    S = input().strip()
    T = input().strip()

    f = [-1] * 26

    for a, b in zip(S, T):
        u = ord(a) - ord('a')
        v = ord(b) - ord('a')

        if f[u] == -1:
            f[u] = v
        elif f[u] != v:
            print(-1)
            return

    active_count = sum(1 for x in range(26) if f[x] != -1)

    base = 0
    for x in range(26):
        if f[x] != -1 and f[x] != x:
            base += 1

    incoming = [[] for _ in range(26)]
    for x in range(26):
        if f[x] != -1:
            incoming[f[x]].append(x)

    # If all 26 letters appear in S, there is no initially empty letter.
    # In that case, a non-identity permutation cannot be changed at all.
    if active_count == 26:
        if len(set(f)) == 26 and base > 0:
            print(-1)
            return

    state = [0] * 26
    index_in_path = [-1] * 26
    extra = 0

    for start in range(26):
        if f[start] == -1 or f[start] == start:
            continue
        if state[start] != 0:
            continue

        cur = start
        path = []

        while True:
            if f[cur] == -1 or f[cur] == cur:
                for node in path:
                    state[node] = 2
                break

            if state[cur] == 0:
                state[cur] = 1
                index_in_path[cur] = len(path)
                path.append(cur)
                cur = f[cur]

            elif state[cur] == 1:
                cycle_start = index_in_path[cur]
                cycle_nodes = path[cycle_start:]
                cycle_set = set(cycle_nodes)

                pure = True
                for v in cycle_nodes:
                    for x in incoming[v]:
                        if x not in cycle_set:
                            pure = False
                            break
                    if not pure:
                        break

                if pure:
                    extra += 1

                for node in path:
                    state[node] = 2
                break

            else:
                for node in path:
                    state[node] = 2
                break

    print(base + extra)


if __name__ == "__main__":
    main()
