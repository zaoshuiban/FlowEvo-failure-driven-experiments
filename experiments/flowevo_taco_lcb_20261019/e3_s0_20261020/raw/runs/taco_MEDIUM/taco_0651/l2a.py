import sys

def evenForest(t_nodes, t_edges, t_from, t_to):
    graph = [[] for _ in range(t_nodes + 1)]

    for u, v in zip(t_from, t_to):
        graph[u].append(v)
        graph[v].append(u)

    parent = [0] * (t_nodes + 1)
    order = [1]
    parent[1] = -1

    for node in order:
        for neighbor in graph[node]:
            if neighbor != parent[node]:
                parent[neighbor] = node
                order.append(neighbor)

    subtree_size = [1] * (t_nodes + 1)

    for node in reversed(order):
        if parent[node] != -1:
            subtree_size[parent[node]] += subtree_size[node]

    removed_edges = 0

    for node in range(2, t_nodes + 1):
        if subtree_size[node] % 2 == 0:
            removed_edges += 1

    return removed_edges


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t_nodes, t_edges = data[0], data[1]

    t_from = []
    t_to = []

    index = 2
    for _ in range(t_edges):
        t_from.append(data[index])
        t_to.append(data[index + 1])
        index += 2

    print(evenForest(t_nodes, t_edges, t_from, t_to))


if __name__ == "__main__":
    main()