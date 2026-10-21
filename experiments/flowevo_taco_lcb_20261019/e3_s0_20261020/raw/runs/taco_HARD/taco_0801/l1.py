import sys
from collections import Counter, deque


def solve() -> None:
    input = sys.stdin.readline

    t = input().strip()
    n = int(input())

    need = Counter(t)

    # Nodes:
    # 0: source
    # 1..n: given strings
    # n+1..n+26: letters
    # n+27: sink
    source = 0
    sink = n + 27
    nodes = sink + 1

    graph = [[] for _ in range(nodes)]

    def add_edge(u, v, cap, cost):
        graph[u].append([v, cap, cost, len(graph[v])])
        graph[v].append([u, 0, -cost, len(graph[u]) - 1])

    # Letter nodes to sink
    for c in range(26):
        cnt = need.get(chr(ord('a') + c), 0)
        if cnt > 0:
            add_edge(n + 1 + c, sink, cnt, 0)

    # Source to strings, strings to letters
    for i in range(1, n + 1):
        s, a = input().split()
        a = int(a)

        cap = min(a, len(s))
        if cap > 0:
            add_edge(source, i, cap, i)  # cost is i rubles

        counts = Counter(s)
        for ch, cnt in counts.items():
            letter_node = n + 1 + (ord(ch) - ord('a'))
            add_edge(i, letter_node, cnt, 0)

    required = len(t)
    if required == 0:
        print(0)
        return

    flow = 0
    total_cost = 0
    INF = 10**18

    while flow < required:
        dist = [INF] * nodes
        parent_v = [-1] * nodes
        parent_e = [-1] * nodes
        in_queue = [False] * nodes

        dist[source] = 0
        q = deque([source])
        in_queue[source] = True

        while q:
            v = q.popleft()
            in_queue[v] = False

            for ei, edge in enumerate(graph[v]):
                to, cap, cost, _ = edge
                if cap > 0 and dist[to] > dist[v] + cost:
                    dist[to] = dist[v] + cost
                    parent_v[to] = v
                    parent_e[to] = ei
                    if not in_queue[to]:
                        in_queue[to] = True
                        q.append(to)

        if dist[sink] == INF:
            break

        add = required - flow
        v = sink

        while v != source:
            pv = parent_v[v]
            edge = graph[pv][parent_e[v]]
            add = min(add, edge[1])
            v = pv

        v = sink
        while v != source:
            pv = parent_v[v]
            ei = parent_e[v]
            edge = graph[pv][ei]

            edge[1] -= add
            graph[v][edge[3]][1] += add

            v = pv

        flow += add
        total_cost += add * dist[sink]

    if flow == required:
        print(total_cost)
    else:
        print(-1)


if __name__ == "__main__":
    solve()