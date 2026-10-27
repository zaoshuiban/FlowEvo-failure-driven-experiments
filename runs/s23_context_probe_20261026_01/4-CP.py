import sys

def solve():
    input = sys.stdin.readline
    n = int(input())
    parents = list(map(int, input().split()))

    children = [[] for _ in range(n)]
    for i, p in enumerate(parents, start=1):
        children[p - 1].append(i)

    # depth parity determines when an apple reaches node 1.
    # We simulate annihilation using sets of depths present in subtree.
    # For each node, keep set of depths (relative to node) of apples that
    # arrive at this node at the same time. Actually simpler: compute for
    # each node the set of depths of leaves? Let's use known solution:
    # answer = number of distinct depths (distance from root) that have odd count?
    # Correct known approach: For each node, maintain set of depths of apples
    # that reach it. Merge children sets with symmetric difference, then add
    # current node's own depth. Answer is size of set at root.

    depth = [0] * n
    order = [0]
    for v in order:
        for c in children[v]:
            depth[c] = depth[v] + 1
            order.append(c)

    sets = [None] * n
    for v in reversed(order):
        s = set()
        for c in children[v]:
            cs = sets[c]
            if len(cs) > len(s):
                s, cs = cs, s
            for x in cs:
                if x in s:
                    s.remove(x)
                else:
                    s.add(x)
        # apple starting at v has depth depth[v]; it reaches v at time 0
        # We store absolute depth of origin? Use depth from root.
        d = depth[v]
        if d in s:
            s.remove(d)
        else:
            s.add(d)
        sets[v] = s

    print(len(sets[0]))

if __name__ == "__main__":
    solve()