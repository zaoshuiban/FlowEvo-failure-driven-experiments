import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]

    def add_edge(self, u, v, cap):
        self.graph[u].append([v, cap, len(self.graph[v])])
        self.graph[v].append([u, 0, len(self.graph[u]) - 1])

    def max_flow(self, source, sink):
        flow = 0
        INF = 10**18
        n = self.n
        graph = self.graph

        while True:
            level = [-1] * n
            level[source] = 0
            q = deque([source])

            while q:
                u = q.popleft()
                for v, cap, _ in graph[u]:
                    if cap > 0 and level[v] == -1:
                        level[v] = level[u] + 1
                        q.append(v)

            if level[sink] == -1:
                break

            it = [0] * n

            def dfs(u, pushed):
                if u == sink:
                    return pushed

                while it[u] < len(graph[u]):
                    edge = graph[u][it[u]]
                    v, cap, rev = edge

                    if cap > 0 and level[v] == level[u] + 1:
                        sent = dfs(v, min(pushed, cap))
                        if sent:
                            edge[1] -= sent
                            graph[v][rev][1] += sent
                            return sent

                    it[u] += 1

                return 0

            while True:
                pushed = dfs(source, INF)
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

    processes = data[idx:idx + n]
    idx += n

    b = data[idx]
    idx += 1

    batches = []
    total_batch_processes = 0

    for _ in range(b):
        s = data[idx]
        idx += 1

        systems = data[idx:idx + s]
        idx += s

        p = data[idx]
        idx += 1

        batches.append((systems, p))
        total_batch_processes += p

    source = 0
    batch_start = 1
    system_start = batch_start + b
    sink = system_start + n

    dinic = Dinic(sink + 1)
    INF = 10**15

    for i, (systems, p) in enumerate(batches):
        batch_node = batch_start + i
        dinic.add_edge(source, batch_node, p)

        for system in systems:
            system_node = system_start + (system - 1)
            dinic.add_edge(batch_node, system_node, INF)

    for i, cost in enumerate(processes):
        system_node = system_start + i
        dinic.add_edge(system_node, sink, cost)

    min_cut = dinic.max_flow(source, sink)
    answer = total_batch_processes - min_cut

    print(max(0, answer))


if __name__ == "__main__":
    main()