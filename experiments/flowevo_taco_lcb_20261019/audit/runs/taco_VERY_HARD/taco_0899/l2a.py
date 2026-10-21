import sys


def solve():
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
        m = next_int()

        adj = [[] for _ in range(n)]

        for _ in range(m):
            u = next_int() - 1
            v = next_int() - 1
            adj[u].append(v)
            adj[v].append(u)

        # Maximum Cardinality Search on a chordal graph.
        # The maximum clique size is max(1 + already selected neighbours).
        counts = [0] * n
        selected = bytearray(n)
        buckets = [[] for _ in range(n + 1)]
        buckets[0] = list(range(n))

        current_max = 0
        answer = 0

        for _ in range(n):
            v = -1

            while current_max >= 0:
                bucket = buckets[current_max]
                while bucket:
                    x = bucket.pop()
                    if not selected[x] and counts[x] == current_max:
                        v = x
                        break
                if v != -1:
                    break
                current_max -= 1

            selected[v] = 1
            clique_size = counts[v] + 1
            if clique_size > answer:
                answer = clique_size

            for w in adj[v]:
                if not selected[w]:
                    old = counts[w]
                    new = old + 1
                    counts[w] = new
                    buckets[new].append(w)
                    if new > current_max:
                        current_max = new

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()