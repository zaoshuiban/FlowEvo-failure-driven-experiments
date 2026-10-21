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

    if n == 1:
        print("0.000000000000000")
        return

    parent = [-1] * n
    probability = [0.0] * n
    probability[0] = 1.0

    stack = [0]
    answer = 0.0

    while stack:
        u = stack.pop()

        if u == 0:
            child_count = len(adj[u])
        else:
            child_count = len(adj[u]) - 1

        if child_count == 0:
            continue

        next_probability = probability[u] / child_count

        for v in adj[u]:
            if v == parent[u]:
                continue

            parent[v] = u
            probability[v] = next_probability
            answer += next_probability
            stack.append(v)

    print(f"{answer:.15f}")


if __name__ == "__main__":
    main()