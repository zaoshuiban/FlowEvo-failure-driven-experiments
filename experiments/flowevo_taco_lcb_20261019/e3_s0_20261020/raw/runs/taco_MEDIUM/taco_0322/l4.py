import sys
from collections import deque

sys.setrecursionlimit(1_000_000)


class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]
        self.level = [-1] * n
        self.it = [0] * n

    def add_edge(self, u, v, cap):
        self.graph[u].append([v, cap, len(self.graph[v])])
        self.graph[v].append([u, 0, len(self.graph[u]) - 1])

    def bfs(self, source, sink):
        self.level = [-1] * self.n
        self.level[source] = 0
        q = deque([source])

        while q:
            u = q.popleft()
            for v, cap, _ in self.graph[u]:
                if cap > 0 and self.level[v] == -1:
                    self.level[v] = self.level[u] + 1
                    q.append(v)

        return self.level[sink] != -1

    def dfs(self, u, sink, pushed):
        if u == sink:
            return pushed

        while self.it[u] < len(self.graph[u]):
            edge = self.graph[u][self.it[u]]
            v, cap, rev = edge

            if cap > 0 and self.level[v] == self.level[u] + 1:
                flow = self.dfs(v, sink, min(pushed, cap))
                if flow:
                    edge[1] -= flow
                    self.graph[v][rev][1] += flow
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


def solve_case(n, prateek, batches):
    b = len(batches)

    source = n + b
    sink = source + 1
    total_nodes = sink + 1

    dinic = Dinic(total_nodes)
    INF = 10**18

    for i in range(n):
        dinic.add_edge(i, sink, prateek[i])

    total_processes = 0

    for i, (systems, p) in enumerate(batches):
        batch_node = n + i
        total_processes += p

        dinic.add_edge(source, batch_node, p)

        for system in set(systems):
            dinic.add_edge(batch_node, system - 1, INF)

    min_cut = dinic.max_flow(source, sink)
    return total_processes - min_cut


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    answers = []

    while idx < len(data):
        n = data[idx]
        idx += 1

        prateek = data[idx:idx + n]
        idx += n

        if idx < len(data):
            b = data[idx]
            idx += 1
        else:
            b = 0

        batches = []

        for _ in range(b):
            s = data[idx]
            idx += 1

            systems = data[idx:idx + s]
            idx += s

            p = data[idx]
            idx += 1

            batches.append((systems, p))

        answers.append(str(solve_case(n, prateek, batches)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()