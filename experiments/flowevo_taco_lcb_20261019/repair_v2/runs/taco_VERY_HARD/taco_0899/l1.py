import sys


def solve() -> None:
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int() -> int:
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
        counts = [0] * n
        selected = bytearray(n)
        buckets = [[] for _ in range(n + 1)]
        buckets[0].extend(range(n))

        max_count = 0
        answer = 1

        for _step in range(n):
            while True:
                bucket = buckets[max_count]
                while bucket:
                    v = bucket.pop()
                    if not selected[v] and counts[v] == max_count:
                        break
                else:
                    max_count -= 1
                    continue
                break

            selected[v] = 1
            if max_count + 1 > answer:
                answer = max_count + 1

            for w in adj[v]:
                if not selected[w]:
                    counts[w] += 1
                    new_count = counts[w]
                    buckets[new_count].append(w)
                    if new_count > max_count:
                        max_count = new_count

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()