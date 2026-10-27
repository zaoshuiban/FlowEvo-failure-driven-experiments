import sys

def solve():
    input = sys.stdin.readline
    n = int(input())
    parents = list(map(int, input().split()))
    children = [[] for _ in range(n)]
    for i, p in enumerate(parents, start=1):
        children[p - 1].append(i)

    # dp[v] = set of times (distance from v) at which an apple reaches v
    # from the subtree of v, after annihilation within the subtree.
    dp = [None] * n

    for v in range(n - 1, -1, -1):
        s = set()
        for c in children[v]:
            cs = dp[c]
            # shift child's times by +1 (edge v-c)
            # merge into s with symmetric difference
            if len(cs) > len(s):
                # iterate over smaller (s), toggle into larger (cs shifted)
                # but we need shifted cs; do it by iterating over s and toggling in cs
                # then swap roles: result should be shifted cs XOR s
                # Simpler: ensure we iterate over smaller set.
                # We'll build new set by iterating over smaller.
                small, big = s, cs
                # We want result = (big shifted by 1) XOR small
                # Iterate over small, toggle (t+1) in big, then shift big? No.
                # Instead: iterate over small, toggle t in a shifted view.
                # To avoid shifting big, note: result times = {x+1 : x in big} XOR small.
                # We can iterate over small and toggle (t) in big after shifting big.
                # Shifting big costs O(|big|). But small-to-large: we iterate over small.
                # We can shift big in place by rebuilding? That's O(|big|) anyway.
                # Better: keep sets unshifted relative to v? Let's just do standard:
                # iterate over smaller set, toggle (t+1) in larger set.
                # But larger set is cs (unshifted). We need to toggle t+1 in cs.
                # That's fine: for t in s: toggle t+1 in cs. Then s = cs.
                # But then cs is modified; that's okay since we won't use it again.
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

    # At root (node 0), apples at time t>0 reach root at time t.
    # Time 0 apple is the one initially at root, collected immediately.
    # Actually dp[0] contains times relative to node 0 when apples are at node 0.
    # The apple initially at 0 is at time 0. Others arrive at time t.
    # Each time t with an apple at root gives one apple collected.
    # But note: apples at root at time 0 is the initial one.
    # dp[0] already includes 0 for initial apple.
    # So answer is size of dp[0]? Let's check: dp[0] is set of times when an apple is at root.
    # Each such time yields one apple collected (since at most one per time).
    # So answer = len(dp[0]).
    print(len(dp[0]))

if __name__ == "__main__":
    solve()