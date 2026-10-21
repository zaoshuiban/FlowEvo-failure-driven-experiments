import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]

    def add_edge(self, u, v, cap):
        forward = [v, cap, len(self.graph[v])]
        backward = [u, 0, len(self.graph[u])]
        self.graph[u].append(forward)
        self.graph[v].append(backward)

    def bfs(self, source, sink, level):
        for i in range(self.n):
            level[i] = -1

        q = deque([source])
        level[source] = 0

        while q:
            u = q.popleft()

            for v, cap, rev in self.graph[u]:
                if cap > 0 and level[v] == -1:
                    level[v] = level[u] + 1
                    q.append(v)

        return level[sink] != -1

    def dfs(self, u, sink, pushed, level, ptr):
        if u == sink:
            return pushed

        while ptr[u] < len(self.graph[u]):
            edge = self.graph[u][ptr[u]]
            v, cap, rev = edge

            if cap > 0 and level[v] == level[u] + 1:
                flow = self.dfs(v, sink, min(pushed, cap), level, ptr)

                if flow > 0:
                    edge[1] -= flow
                    self.graph[v][rev][1] += flow
                    return flow

            ptr[u] += 1

        return 0

    def max_flow(self, source, sink):
        flow = 0
        level = [-1] * self.n
        INF = 10**18

        while self.bfs(source, sink, level):
            ptr = [0] * self.n

            while True:
                pushed = self.dfs(source, sink, INF, level, ptr)
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

    prateek = data[idx:idx + n]
    idx += n

    b = data[idx]
    idx += 1

    batches = []

    for _ in range(b):
        s = data[idx]
        idx += 1

        systems = data[idx:idx + s]
        idx += s

        p = data[idx]
        idx += 1

        batches.append((systems, p))

    source = 0
    batch_start = 1
    system_start = 1 + b
    sink = 1 + b + n
    total_nodes = sink + 1

    dinic = Dinic(total_nodes)

    INF = 10**15
    total_positive = 0

    for i, (systems, p) in enumerate(batches):
        batch_node = batch_start + i
        dinic.add_edge(source, batch_node, p)
        total_positive += p

        for system in systems:
            system_node = system_start + system - 1
            dinic.add_edge(batch_node, system_node, INF)

    for i, cost in enumerate(prateek):
        system_node = system_start + i
        dinic.add_edge(system_node, sink, cost)

    min_cut = dinic.max_flow(source, sink)
    answer = total_positive - min_cut

    print(max(0, answer))


if __name__ == "__main__":
    main()