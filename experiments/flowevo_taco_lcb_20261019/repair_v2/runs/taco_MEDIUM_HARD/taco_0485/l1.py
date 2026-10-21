import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    edges = []
    for _ in range(n - 1):
        u = next(it) - 1
        v = next(it) - 1
        edges.append((u, v))

    colors = [next(it) for _ in range(n)]

    bad_edges = []
    for u, v in edges:
        if colors[u] != colors[v]:
            bad_edges.append((u, v))

    if not bad_edges:
        print("YES")
        print(1)
        return

    candidates = [bad_edges[0][0], bad_edges[0][1]]

    for root in candidates:
        ok = True
        for u, v in bad_edges:
            if u != root and v != root:
                ok = False
                break

        if ok:
            print("YES")
            print(root + 1)
            return

    print("NO")


if __name__ == "__main__":
    main()