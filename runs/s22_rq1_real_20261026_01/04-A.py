import sys

def solve():
    input = sys.stdin.readline
    n = int(input())
    parents = list(map(int, input().split()))
    children = [[] for _ in range(n)]
    for i, p in enumerate(parents, start=1):
        children[p - 1].append(i)

    # dp[v] = set of times (distance from v) at which an apple reaches v
    # from the subtree of v, after annihilation inside the subtree.
    dp = [None] * n

    for v in range(n - 1, -1, -1):
        s = set()
        for c in children[v]:
            cs = dp[c]
            # shift child's times by +1 (edge v-c)
            # merge into s with symmetric difference
            if len(cs) > len(s):
                # swap roles: shift the smaller set (s) by +1 and merge into cs
                # but shifting s by +1 means new times t+1; merging into cs
                # We'll iterate over s (smaller) and toggle t+1 in cs.
                for t in s:
                    nt = t + 1
                    if nt in cs:
                        cs.remove(nt)
                    else:
                        cs.add(nt)
                s = cs
            else:
                for t in cs:
                    nt = t + 1
                    if nt in s:
                        s.remove(nt)
                    else:
                        s.add(nt)
        # apple initially at v arrives at time 0
        if 0 in s:
            s.remove(0)
        else:
            s.add(0)
        dp[v] = s

    # At root (node 0), apples arriving at time t >= 1 are collected.
    # Time 0 apple is the one initially at root, also collected.
    # But dp[0] contains times when apples reach root after annihilation.
    # Each time in dp[0] corresponds to one apple collected.
    print(len(dp[0]))

if __name__ == "__main__":
    solve()