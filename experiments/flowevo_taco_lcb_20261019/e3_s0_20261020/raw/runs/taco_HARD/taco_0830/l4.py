import sys


def main():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()
        k = next_int()

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = next_int()
            v = next_int()
            adj[u].append(v)
            adj[v].append(u)

        # If k = 1, the empty set is already good.
        # Every non-empty subtree has at least one vertex.
        if k == 1:
            answers.append("0")
            continue

        # Find one endpoint of a diameter.
        far = 1
        max_dist = 0
        stack = [(1, 0, 0)]  # vertex, parent, distance

        while stack:
            u, p, d = stack.pop()
            if d > max_dist:
                max_dist = d
                far = u
            for v in adj[u]:
                if v != p:
                    stack.append((v, u, d + 1))

        start = far

        # Find the other diameter endpoint and root the tree at 'start'.
        parent = [0] * (n + 1)
        order = []
        far = start
        diameter = 0
        stack = [(start, 0, 0)]

        while stack:
            u, p, d = stack.pop()
            parent[u] = p
            order.append(u)

            if d > diameter:
                diameter = d
                far = u

            for v in adj[u]:
                if v != p:
                    stack.append((v, u, d + 1))

        end = far
        base_size = diameter + 1

        # A path between two vertices has exactly two leaves.
        if k <= base_size:
            answers.append("2")
            continue

        # Mark the chosen diameter path.
        on_path = bytearray(n + 1)
        v = end
        while v != 0:
            on_path[v] = 1
            v = parent[v]

        height = [0] * (n + 1)
        gains = []

        # Heavy-chain decomposition of all components hanging off the diameter path.
        for u in reversed(order):
            if on_path[u]:
                continue

            best = -1
            best_child = 0

            for v in adj[u]:
                if parent[v] == u:
                    cand = height[v] + 1
                    if cand > best:
                        best = cand
                        best_child = v

            height[u] = 0 if best < 0 else best

            for v in adj[u]:
                if parent[v] == u and v != best_child:
                    gains.append(height[v] + 1)

            p = parent[u]
            if p and on_path[p]:
                gains.append(height[u] + 1)

        gains.sort(reverse=True)

        current_size = base_size
        answer = 2  # two diameter endpoints

        for g in gains:
            current_size += g
            answer += 1
            if current_size >= k:
                break

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()