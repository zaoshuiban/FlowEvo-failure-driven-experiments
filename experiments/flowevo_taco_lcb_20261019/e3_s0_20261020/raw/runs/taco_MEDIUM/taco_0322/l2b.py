import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]
        self.level = [-1] * n
        self.it = [0] * n

    def add_edge(self, u, v, cap):
        self.graph[u].append([v, len(self.graph[v]), cap])
        self.graph[v].append([u, len(self.graph[u]) - 1, 0])

    def bfs(self, source, sink):
        self.level = [-1] * self.n
        self.level[source] = 0
        q = deque([source])

        while q:
            u = q.popleft()
            for v, rev, cap in self.graph[u]:
                if cap > 0 and self.level[v] == -1:
                    self.level[v] = self.level[u] + 1
                    q.append(v)

        return self.level[sink] != -1

    def dfs(self, u, sink, pushed):
        if u == sink:
            return pushed

        while self.it[u] < len(self.graph[u]):
            edge = self.graph[u][self.it[u]]
            v, rev, cap = edge

            if cap > 0 and self.level[v] == self.level[u] + 1:
                flow = self.dfs(v, sink, min(pushed, cap))
                if flow:
                    edge[2] -= flow
                    self.graph[v][rev][2] += flow
                    return flow

            self.it[u] += 1

        return 0

    def max_flow(self, source, sink):
        flow = 0
        INF = 10**18

        while self.bfs(source, sink):
            self.it = [0] * self.n
            while True:
                pushed = self.dfs(source, sink, INF)
                if pushed == 0:
                    break
                flow += pushed

        return flow


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    systems_cost = []
    for _ in range(n):
        systems_cost.append(data[idx])
        idx += 1

    b = data[idx]
    idx += 1

    batches = []
    total_positive = 0

    for _ in range(b):
        s = data[idx]
        idx += 1

        systems = []
        for _ in range(s):
            systems.append(data[idx] - 1)
            idx += 1

        p = data[idx]
        idx += 1

        batches.append((systems, p))
        total_positive += p

    source = n + b
    sink = source + 1
    total_nodes = sink + 1

    dinic = Dinic(total_nodes)
    INF = 10**15

    for i in range(n):
        if systems_cost[i] > 0:
            dinic.add_edge(i, sink, systems_cost[i])

    for i, (systems, p) in enumerate(batches):
        batch_node = n + i

        if p > 0:
            dinic.add_edge(source, batch_node, p)

        for system in systems:
            dinic.add_edge(batch_node, system, INF)

    min_cut = dinic.max_flow(source, sink)
    answer = total_positive - min_cut

    print(answer)


if __name__ == "__main__":
    main()