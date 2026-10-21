import sys

data = sys.stdin.buffer.read()
ptr = 0
data_len = len(data)


def next_int():
    global ptr
    while ptr < data_len and data[ptr] <= 32:
        ptr += 1
    num = 0
    while ptr < data_len and data[ptr] > 32:
        num = num * 10 + (data[ptr] - 48)
        ptr += 1
    return num


def solve():
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

        labels = [0] * n
        used = bytearray(n)

        buckets = [[] for _ in range(n + 1)]
        for i in range(n):
            buckets[0].append(i)

        max_label = 0
        answer = 1
        selected = 0

        while selected < n:
            while max_label >= 0:
                bucket = buckets[max_label]

                while bucket:
                    v = bucket[-1]
                    if used[v] or labels[v] != max_label:
                        bucket.pop()
                    else:
                        break

                if bucket:
                    v = bucket.pop()
                    break

                max_label -= 1

            used[v] = 1
            current_label = max_label

            if current_label + 1 > answer:
                answer = current_label + 1

            for u in adj[v]:
                if not used[u]:
                    old_label = labels[u]
                    new_label = old_label + 1
                    labels[u] = new_label
                    buckets[new_label].append(u)

                    if new_label > max_label:
                        max_label = new_label

            selected += 1

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()