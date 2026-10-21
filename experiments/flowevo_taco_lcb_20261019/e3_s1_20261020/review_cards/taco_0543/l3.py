import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    adj = [[] for _ in range(n)]

    idx = 1
    for _ in range(n - 1):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        adj[u].append(v)
        adj[v].append(u)

    parent = [-1] * n
    order = [0]
    i = 0

    while i < len(order):
        u = order[i]
        i += 1

        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)

    probability = [0.0] * n
    probability[0] = 1.0
    answer = 0.0

    for u in order:
        if u == 0:
            choices = len(adj[u])
        else:
            choices = len(adj[u]) - 1

        if choices > 0:
            next_probability = probability[u] / choices

            for v in adj[u]:
                if v != parent[u]:
                    probability[v] = next_probability
                    answer += next_probability

    print(f"{answer:.15f}")


if __name__ == "__main__":
    main()