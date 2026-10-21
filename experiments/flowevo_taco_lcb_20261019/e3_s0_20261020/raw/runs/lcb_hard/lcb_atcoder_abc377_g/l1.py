import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    strings = data[1:1 + n]

    INF = 10**18

    # Trie nodes: children[node][character] = next node
    children = [{}]
    # best[node] = minimum length among already inserted strings
    # that have this node as a prefix.
    best = [INF]

    answers = []

    for s in strings:
        length = len(s)

        node = 0
        depth = 0
        path = [0]

        # Query using only strings inserted before s.
        current_min = best[0]

        for ch in s:
            depth += 1
            nxt = children[node].get(ch)

            if nxt is None:
                nxt = len(children)
                children[node][ch] = nxt
                children.append({})
                best.append(INF)

            node = nxt
            path.append(node)

            value = best[node] - 2 * depth
            if value < current_min:
                current_min = value

        if current_min < 0:
            answers.append(str(length + current_min))
        else:
            answers.append(str(length))

        # Insert s into the trie.
        for u in path:
            if length < best[u]:
                best[u] = length

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()