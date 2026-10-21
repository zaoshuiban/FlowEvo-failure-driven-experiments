import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    order = sorted(range(n), key=a.__getitem__)

    p = [0] * n
    for rank, pos in enumerate(order):
        p[pos] = rank

    visited = [False] * n
    groups = []

    for i in range(n):
        if not visited[i]:
            cycle = []
            cur = i
            while not visited[cur]:
                visited[cur] = True
                cycle.append(cur + 1)
                cur = p[cur]
            groups.append(cycle)

    out = [str(len(groups))]
    for cycle in groups:
        out.append(str(len(cycle)) + " " + " ".join(map(str, cycle)))

    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    main()