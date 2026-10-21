import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    adj = [bytearray(n) for _ in range(n)]

    pos = 2
    for _ in range(m):
        u = data[pos] - 1
        v = data[pos + 1] - 1
        pos += 2
        adj[u][v] = 1
        adj[v][u] = 1

    u = v = -1
    for i in range(n):
        row = adj[i]
        for j in range(i + 1, n):
            if row[j] == 0:
                u, v = i, j
                break
        if u != -1:
            break

    if u == -1:
        sys.stdout.write("Yes\n" + "b" * n + "\n")
        return

    color = ['b'] * n
    color[u] = 'a'
    color[v] = 'c'

    ok = True

    for i in range(n):
        if i == u or i == v:
            continue

        nonadj_u = (adj[u][i] == 0)
        nonadj_v = (adj[v][i] == 0)

        if nonadj_u and nonadj_v:
            ok = False
            break
        elif nonadj_u:
            color[i] = 'c'
        elif nonadj_v:
            color[i] = 'a'
        else:
            color[i] = 'b'

    if ok:
        for i in range(n):
            for j in range(i + 1, n):
                expected_edge = not (
                    (color[i] == 'a' and color[j] == 'c') or
                    (color[i] == 'c' and color[j] == 'a')
                )

                if (adj[i][j] == 1) != expected_edge:
                    ok = False
                    break
            if not ok:
                break

    if ok:
        sys.stdout.write("Yes\n" + "".join(color) + "\n")
    else:
        sys.stdout.write("No\n")


if __name__ == "__main__":
    main()