import sys
from array import array


class FastScanner:
    __slots__ = ("data", "idx", "length")

    def __init__(self):
        self.data = sys.stdin.buffer.read()
        self.idx = 0
        self.length = len(self.data)

    def next_int(self):
        data = self.data
        n = self.length
        i = self.idx

        while i < n and data[i] <= 32:
            i += 1

        value = 0
        while i < n and data[i] > 32:
            value = value * 10 + (data[i] - 48)
            i += 1

        self.idx = i
        return value


def solve():
    fs = FastScanner()
    if fs.length == 0:
        return

    t = fs.next_int()
    answers = []

    for _ in range(t):
        n = fs.next_int()
        k = fs.next_int()

        head = array("i", [-1]) * (n + 1)
        m = 2 * (n - 1)
        to = array("i", [0]) * m
        nxt = array("i", [0]) * m

        edge_idx = 0
        for _ in range(n - 1):
            u = fs.next_int()
            v = fs.next_int()

            to[edge_idx] = v
            nxt[edge_idx] = head[u]
            head[u] = edge_idx
            edge_idx += 1

            to[edge_idx] = u
            nxt[edge_idx] = head[v]
            head[v] = edge_idx
            edge_idx += 1

        parent = array("i", [0]) * (n + 1)
        parent[1] = -1

        order = array("i", [0]) * n
        order[0] = 1
        order_size = 1

        stack = [1]

        while stack:
            u = stack.pop()
            e = head[u]
            pu = parent[u]

            while e != -1:
                v = to[e]
                if v != pu:
                    parent[v] = u
                    order[order_size] = v
                    order_size += 1
                    stack.append(v)
                e = nxt[e]

        height = array("i", [1]) * (n + 1)
        answer = 0

        for i in range(n - 1, -1, -1):
            u = order[i]
            hu = height[u]

            if hu <= k:
                answer += 1

            p = parent[u]
            if p > 0:
                new_height = hu + 1
                if new_height > height[p]:
                    height[p] = new_height

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()