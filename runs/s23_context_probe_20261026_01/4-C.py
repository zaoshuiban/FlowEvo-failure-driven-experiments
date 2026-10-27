import sys

def solve():
    input = sys.stdin.readline
    n = int(input())
    parents = list(map(int, input().split()))

    children = [[] for _ in range(n)]
    for i, p in enumerate(parents, start=1):
        children[p - 1].append(i)

    # dp[v] = parity (0/1) of number of apples that reach v from its subtree
    # at the moment apples from v's subtree arrive at v.
    # We process bottom-up.
    dp = [0] * n

    for v in range(n - 1, -1, -1):
        # Apple initially at v contributes 1.
        # Each child c sends dp[c] apples to v (parity).
        # But timing: apples from different depths arrive at different times,
        # so we need to account for depth parity.
        #
        # Key observation: an apple starting at node u reaches v after
        # (depth[u] - depth[v]) seconds. At v, apples arriving at the same
        # time annihilate in pairs. So for each time t, count apples arriving
        # at v at time t, take parity, then those continue upward.
        #
        # Equivalent: for each node, we need parity of count of descendants
        # at each distance. But since apples move one step per second and
        # annihilation happens at each node at each moment, the process is:
        # at node v, at time t, the number of apples is parity of sum over
        # children of apples that were at child at time t-1, plus initial apple
        # at v at time 0.
        #
        # This is equivalent to: dp[v] = parity of (1 + sum over children of dp[c])
        # BUT with a twist: apples from child c arrive at v one second later,
        # and during that second they might annihilate at c. However, dp[c]
        # already accounts for annihilation at c at the moment they leave c.
        # The issue is that apples from different children arrive at v at
        # different times if their subtrees have different depths.
        #
        # Actually, the correct model: Let f(v, t) = parity of apples at v at time t.
        # f(v, 0) = 1 (initial apple at v).
        # For t >= 1: f(v, t) = parity of sum over children c of f(c, t-1).
        # Answer = sum over t >= 0 of f(1, t) (apples collected at root at each time).
        #
        # We can compute this with a different DP: for each node, we need
        # the sequence of parities over time. But n up to 1e5, so we need
        # efficient merging.
        #
        # Alternative known solution: The answer is the number of nodes v
        # such that the number of ancestors (including v?) ... Actually known
        # result: answer = number of nodes at even depth? No.
        #
        # Let's think: This is equivalent to computing for each node the
        # parity of apples arriving at root. Known trick: use bitsets or
        # small-to-large merging of sets of depths with odd counts.
        #
        # For each node v, maintain a set S_v of depths (relative to v)
        # at which an odd number of apples are present at v.
        # Initially S_v = {0} (apple at v at time 0).
        # When merging child c into v: shift S_c by +1 (since apples take 1 sec
        # to go from c to v), then symmetric difference with S_v.
        # Answer = size of S_root (number of times root has an apple).
        #
        # This is exactly small-to-large merging of sets with shift.
        # To handle shift efficiently, store depths as negative offset or
        # use a global offset per set. Standard trick: store set of (depth - offset)
        # and keep offset per set. When shifting, increment offset.
        #
        # Let's implement: each set stores values (d - offset) where d is actual
        # relative depth. To shift by +1, offset += 1.
        # Merging: for each element x in smaller set, actual depth = x + offset_small.
        # We want to add to larger set: actual depth in larger's terms = actual depth.
        # So we insert (actual_depth - offset_large) into larger set.
        # Symmetric difference: if already present, remove; else add.

        # Initialize with {0} for node v: actual depth 0, offset 0, store 0.
        s = {0}
        offset = 0

        for c in children[v]:
            cs = sets[c]
            coff = offsets[c]
            # shift child's set by +1: coff += 1
            coff += 1
            # merge cs into s (symmetric difference)
            if len(cs) > len(s):
                # swap, but need to adjust offsets
                # We want to merge s into cs. After swap, s is larger.
                # But offsets differ. Let's just always merge smaller into larger.
                # To avoid confusion, we'll merge cs into s if len(cs) <= len(s),
                # else swap roles.
                s, cs = cs, s
                offset, coff = coff, offset
            # now merge cs (smaller) into s (larger)
            for x in cs:
                actual = x + coff
                y = actual - offset
                if y in s:
                    s.remove(y)
                else:
                    s.add(y)
        sets[v] = s
        offsets[v] = offset

    # Answer = size of set at root (number of times root has odd apple count)
    # But wait: root collects apple at time t if f(1, t) = 1.
    # The set S_root contains relative depths (times) where odd count.
    # So answer = len(S_root).
    print(len(sets[0]))

if __name__ == "__main__":
    solve()