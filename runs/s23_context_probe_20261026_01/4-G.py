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
                # make s the larger; but we need to shift cs, not s.
                # So instead iterate over smaller and toggle in larger.
                # Here cs is larger, so iterate over s (smaller), toggling in cs shifted.
                # Simpler: ensure we iterate over the smaller set.
                small, big = s, cs
                # We want to merge (big) with (small shifted by +1).
                # Iterate over small, toggle (t+1) in big.
                for t in small:
                    nt = t + 1
                    if nt in big:
                        big.remove(nt)
                    else:
                        big.add(nt)
                s = big
            else:
                # cs is smaller or equal; iterate over cs, toggle (t+1) in s
                for t in cs:
                    nt = t + 1
                    if nt in s:
                        s.remove(nt)
                    else:
                        s.add(nt)
        # apple initially at v arrives at v at time 0
        if 0 in s:
            s.remove(0)
        else:
            s.add(0)
        dp[v] = s

    # At root (node 0), apples at time t reach root at time t.
    # But root's own apple is at time 0 and is collected immediately.
    # Actually dp[0] contains times when apples are at root (including time 0 for root's apple).
    # Each such time corresponds to one apple collected.
    print(len(dp[0]))

if __name__ == "__main__":
    solve()