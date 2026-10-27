import sys

MOD = 998244353

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])

    # For a perfectly balanced BST with n nodes, the shape is the complete
    # binary tree (levels filled left to right). The number of such trees
    # depends on the striped condition, which constrains key parities.
    #
    # In a BST, inorder traversal gives keys in increasing order. So assigning
    # keys 1..n is equivalent to assigning inorder positions. The parity of a
    # key equals the parity of its inorder position (1-based).
    #
    # We need to count the number of ways to choose the shape (perfectly
    # balanced) and assign keys such that striped conditions hold.
    #
    # Actually, for a fixed shape, the keys are forced by inorder traversal.
    # So we just need to check if the unique complete tree shape satisfies
    # the striped condition. But wait: there can be multiple perfectly balanced
    # shapes? For sum of depths minimization, the shape is not always unique.
    # For n nodes, the complete tree shape is unique when we require all levels
    # full except last filled left to right. But "perfectly balanced" means
    # minimizing sum of depths. For some n, there are multiple shapes achieving
    # the minimum sum of depths (e.g., n=4: complete tree has left subtree size 2,
    # right size 1; but also left size 1, right size 2 gives same sum? Let's check:
    # n=4, shape A: root with left subtree of 2 nodes (chain), right 1 node.
    # depths: root 0, left child 1, its child 2, right child 1 => sum=4.
    # shape B: root with left 1, right 2 (chain) => depths: 0,1,1,2 => sum=4.
    # Both have sum 4. So multiple perfectly balanced shapes exist!
    #
    # So we need to count over all perfectly balanced shapes and valid key assignments.
    #
    # This is a known problem: count perfectly balanced striped BSTs.
    # Let's derive DP.
    #
    # For a subtree with k nodes, we need to know:
    # - the minimum sum of depths achievable (perfectly balanced)
    # - number of striped BSTs with keys from some range (but keys are determined
    #   by inorder positions, so parity pattern depends on starting parity).
    #
    # Since keys are 1..n, the inorder positions are 1..n. For a subtree, its
    # inorder positions form a contiguous range. The parity of the root's key
    # depends on the size of its left subtree and the starting parity of the range.
    #
    # Let's define DP over subtree size and starting parity (parity of the smallest
    # key in the subtree's range). Actually, the keys in a subtree are a contiguous
    # range of integers. The root's key is at position (left_size + 1) within the range.
    # So root parity = (start_parity + left_size) mod 2.
    #
    # Striped condition:
    # - left child root parity != root parity
    # - right child root parity == root parity
    #
    # For a subtree of size k with starting parity p (0=even, 1=odd for the smallest key),
    # we want to count valid striped BSTs that are perfectly balanced (min sum depths).
    #
    # But we also need to track the minimum sum of depths. Let's define:
    # min_depth_sum[k] = minimum sum of depths for a BST with k nodes.
    # This is achieved by balancing left and right subtree sizes as evenly as possible
    # in terms of depth sum. The formula: for k nodes, we choose left size L and right size R=k-1-L
    # to minimize (min_depth_sum[L] + L) + (min_depth_sum[R] + R) because each node in subtree
    # gets +1 depth. So total = min_depth_sum[L] + min_depth_sum[R] + (k-1).
    # We need to find all L that achieve the minimum.
    #
    # Then DP: dp[k][p] = number of perfectly balanced striped BSTs with k nodes
    # and starting parity p (parity of smallest key in range).
    #
    # Base: k=0: dp[0][p] = 1 (empty tree).
    # k=1: dp[1][p] = 1 (single node, no constraints).
    #
    # For k>=2: root parity r = (p + L) mod 2 where L is left size.
    # Left subtree has size L, starting parity p (same as parent's range start).
    # Right subtree has size R, starting parity = (p + L + 1) mod 2.
    # Constraints:
    # - left child root parity != r. Left child root parity = (p + L_left) mod 2
    #   where L_left is left size of left subtree. But we don't track that directly.
    #   Actually, the left child's root parity is determined by its own subtree's
    #   starting parity and its left size. But in our DP, dp[L][p] counts all valid
    #   left subtrees with starting parity p. The root of left subtree has parity
    #   (p + L_left) mod 2 for some L_left. We need this to be != r.
    #   This is not directly captured by dp[L][p] because dp[L][p] sums over all
    #   valid left subtrees regardless of their root parity.
    #
    # We need to refine DP to track the root parity of the subtree.
    # Let dp[k][p][q] = number of perfectly balanced striped BSTs with k nodes,
    # starting parity p (smallest key parity), and root parity q.
    #
    # Then for k>=2, choose L (left size) and R=k-1-L such that depth sum is minimal.
    # Root parity r = (p + L) mod 2.
    # Left subtree: size L, starting parity p, root parity qL. Constraint: qL != r.
    # Right subtree: size R, starting parity pR = (p + L + 1) mod 2, root parity qR.
    # Constraint: qR == r.
    #
    # dp[k][p][r] = sum over valid L of (sum_{qL != r} dp[L][p][qL]) * (sum_{qR == r} dp[R][pR][qR])
    #
    # We need to compute min_depth_sum[k] and the set of valid L for each k.
    #
    # For n up to 1e6, we need O(n) or O(n log n) algorithm.
    #
    # Let's first compute min_depth_sum[k] for k=0..n.
    # min_depth_sum[0] = 0
    # min_depth_sum[1] = 0
    # For k>=2: min_depth_sum[k] = k-1 + min_{L+R=k-1} (min_depth_sum[L] + min_depth_sum[R])
    #
    # This is like optimal BST shape for sum of depths. The optimal L is around (k-1)/2.
    # Actually, the function min_depth_sum[k] is known: it's achieved by complete tree.
    # But there can be multiple L achieving the minimum. We need all such L.
    #
    # Let's compute min_depth_sum iteratively. For each k, we need to find L in [0, k-1]
    # minimizing f(L) = min_depth_sum[L] + min_depth_sum[k-1-L].
    # Since min_depth_sum is convex? Let's check small values:
    # k=0: 0
    # k=1: 0
    # k=2: 1 + 0+0 = 1 (L=0 or 1)
    # k=3: 2 + min(0+1, 1+0) = 2+1=3 (L=0: 0+1=1, L=1: 0+0=0? wait k-1=2, L=1,R=1: 0+0=0, so 2+0=2? Let's recompute:
    # min_depth_sum[3] = 2 + min over L+R=2 of (min_depth_sum[L]+min_depth_sum[R])
    # L=0,R=2: 0+1=1
    # L=1,R=1: 0+0=0
    # L=2,R=0: 1+0=1
    # min=0, so min_depth_sum[3]=2. Check: tree with 3 nodes, root with two children: depths 0,1,1 sum=2. Yes.
    # k=4: 3 + min over L+R=3:
    # L=0,R=3: 0+2=2
    # L=1,R=2: 0+1=1
    # L=2,R=1: 1+0=1
    # L=3,R=0: 2+0=2
    # min=1, so min_depth_sum[4]=4. (root with left 2-chain, right 1: depths 0,1,2,1 sum=4; or left 1, right 2-chain: 0,1,1,2 sum=4)
    # k=5: 4 + min over L+R=4:
    # L=0,R=4: 0+4=4
    # L=1,R=3: 0+2=2
    # L=2,R=2: 1+1=2
    # L=3,R=1: 2+0=2
    # L=4,R=0: 4+0=4
    # min=2, so min_depth_sum[5]=6. (complete tree: root, 2 children, 2 grandchildren: depths 0,1,1,2,2 sum=6)
    #
    # The optimal L values are those where min_depth_sum[L]+min_depth_sum[k-1-L] is minimal.
    # For large k, the optimal L is around (k-1)/2, but there can be a range.
    # Actually, min_depth_sum[k] is achieved by complete tree, and the optimal L is
    # the left subtree size of the complete tree. But there might be multiple L
    # giving the same sum. For example k=4: L=1 and L=2 both give sum 1.
    # So we need to find all L that achieve the minimum.
    #
    # Since n up to 1e6, we can compute min_depth_sum for all k up to n in O(n) if
    # we can find the optimal L quickly. The function g(L) = min_depth_sum[L] + min_depth_sum[k-1-L]
    # is convex? min_depth_sum is convex (discrete). The sum of two convex functions
    # is convex, so the minimum is achieved on a contiguous range of L.
    # We can find the range by ternary search or by noting that the optimal L is
    # around (k-1)/2. Actually, min_depth_sum[k] is roughly k*log2(k), and the
    # optimal L is the one that makes the tree as balanced as possible.
    #
    # Let's compute min_depth_sum[k] using the formula for complete tree:
    # For k nodes, let h = floor(log2(k)). The complete tree has left subtree size:
    # if k = 2^h - 1 + last, where 0 <= last <= 2^h, then left size = 2^{h-1} - 1 + min(last, 2^{h-1}).
    # But this gives one optimal L. Are there others?
    # For k=4: h=2, 2^2-1=3, last=1. left size = 2^{1}-1 + min(1,2) = 1+1=2. But L=1 also optimal.
    # So the optimal L range is not just one value.
    #
    # Let's analyze min_depth_sum[k]. It's known that min_depth_sum[k] = sum_{i=1}^k floor(log2(i))? No.
    # Actually, for a complete tree, the sum of depths is: sum over levels of (level * nodes at level).
    # For k nodes, the complete tree has levels 0..h-1 full, and last level with 'last' nodes.
    # Sum of depths = sum_{d=0}^{h-1} d * 2^d + h * last.
    # Let's verify: k=4: h=2, last=1. sum = 0*1 + 1*2 + 2*1 = 4. Correct.
    # k=5: h=2, last=2. sum = 0*1 + 1*2 + 2*2 = 6. Correct.
    # k=3: h=1, last=2? 2^1-1=1, last=2. sum = 0*1 + 1*2 = 2. Correct.
    # k=2: h=1, last=1. sum = 0*1 + 1*1 = 1. Correct.
    # k=1: h=0, last=1? 2^0-1=0, last=1. sum = 0*1 = 0. Correct.
    #
    # So min_depth_sum[k] = sum_{d=0}^{h-1} d*2^d + h*last, where h = floor(log2(k)), last = k - (2^h - 1).
    # This is the minimum sum of depths.
    #
    # Now, which L achieve this minimum? We need min_depth_sum[L] + min_depth_sum[R] = min_depth_sum[k] - (k-1).
    # Let's denote S(k) = min_depth_sum[k]. We need S(L) + S(R) = S(k) - (k-1) where L+R=k-1.
    #
    # For a complete tree, the left subtree size L0 is given by the formula above.
    # Are there other L? For k=4, L0=2, but L=1 also works. Let's check:
    # S(1)+S(2) = 0+1=1. S(4)-3 = 4-3=1. Yes.
    # S(2)+S(1) = 1+0=1. Yes.
    # So L=1,2 both work.
    #
    # In general, the optimal L range is [L_min, L_max] where L_min and L_max are
    # the sizes that make the tree as balanced as possible. For a complete tree,
    # the left subtree can be either the "left-heavy" or "right-heavy" version
    # when the last level is not full on one side.
    #
    # Actually, the condition for optimal L is that the resulting tree has the same
    # sum of depths as the complete tree. This happens when the tree is "almost complete"
    # in the sense that all levels except possibly the last are full, and the last level
    # is filled from left to right, but we can also have the last level filled from right to left?
    # No, for BST, the shape is determined by the sizes. The sum of depths only depends on
    # the sizes of subtrees, not on which specific nodes are where. So any L that gives
    # the same S(L)+S(R) is optimal.
    #
    # Let's find the range of optimal L for each k. We can compute S(k) for all k up to n
    # using the formula, then for each k, find the range of L where S(L)+S(k-1-L) = S(k)-(k-1).
    # Since S is convex, the set of optimal L is a contiguous range. We can find it by
    # binary search or by noting that the optimal L is around (k-1)/2.
    #
    # But we need to do this efficiently for all k up to 1e6. We can compute S(k) in O(1) per k.
    # Then for each k, we need to find the range of L. We can use the fact that the optimal L
    # is the one that makes the tree as balanced as possible. The range is determined by
    # the last level distribution.
    #
    # Let's derive the range of optimal L directly.
    # For k nodes, let h = floor(log2(k)), full = 2^h - 1, last = k - full.
    # The complete tree has left subtree size L0 = (2^{h-1} - 1) + min(last, 2^{h-1}) for h>=1.
    # The right subtree size R0 = k-1-L0.
    # The sum of depths is S(k) = S(L0) + S(R0) + (k-1).
    #
    # Are there other L? Consider shifting one node from left to right. The change in
    # S(L)+S(R) when we increase L by 1 (and decrease R by 1) is:
    # delta = (S(L+1)-S(L)) - (S(R)-S(R-1)).
    # Since S is convex, delta is non-decreasing in L. The minimum is where delta crosses 0.
    # So the optimal L range is where delta = 0.
    #
    # We can compute S(k) for all k up to n in O(n) using the formula:
    # S(0)=0, S(1)=0.
    # For k>=2: h = k.bit_length()-1, full = (1<<h)-1, last = k-full.
    # S(k) = sum_{d=0}^{h-1} d*2^d + h*last.
    # We can precompute prefix sums of d*2^d.
    #
    # Then for each k, we need to find the range of L. We can do this by binary search
    # on L for the condition S(L)+S(k-1-L) == S(k)-(k-1). Since the function is convex,
    # we can find the minimum and then expand. But doing binary search for each k would be
    # O(n log n), which is fine for n=1e6 (about 20 million operations).
    #
    # However, we also need to compute the DP. The DP has states dp[k][p][q] for k up to n,
    # p in {0,1}, q in {0,1}. That's 4*n states. For each k, we need to sum over all optimal L.
    # If the range of optimal L is large, this could be O(n^2) in worst case. But the range
    # is typically small (at most 2 or 3 values?). Let's check:
    # For k=4, optimal L: 1,2 (range size 2).
    # For k=5, optimal L: 1,2,3? Let's check S(5)=6, S(5)-4=2.
    # L=0,R=4: S(0)+S(4)=0+4=4 !=2
    # L=1,R=3: 0+2=2 yes
    # L=2,R=2: 1+1=2 yes
    # L=3,R=1: 2+0=2 yes
    # L=4,R=0: 4+0=4 no
    # So L=1,2,3 (range size 3).
    # For k=6: S(6)=? h=2, full=3, last=3. S(6)=0*1+1*2+2*3=8. S(6)-5=3.
    # L=0,R=5: 0+6=6
    # L=1,R=4: 0+4=4
    # L=2,R=3: 1+2=3 yes
    # L=3,R=2: 2+1=3 yes
    # L=4,R=1: 4+0=4
    # L=5,R=0: 6+0=6
    # So L=2,3 (range size 2).
    # For k=7: S(7)=? h=2, full=3, last=4. S(7)=0+2+8=10. S(7)-6=4.
    # L=0,R=6: 0+8=8
    # L=1,R=5: 0+6=6
    # L=2,R=4: 1+4=5
    # L=3,R=3: 2+2=4 yes
    # L=4,R=2: 4+1=5
    # L=5,R=1: 6+0=6
    # L=6,R=0: 8+0=8
    # So L=3 only (range size 1).
    # For k=8: S(8)=? h=3, full=7, last=1. S(8)=0*1+1*2+2*4+3*1=0+2+8+3=13. S(8)-7=6.
    # L=0,R=7: 0+10=10
    # L=1,R=6: 0+8=8
    # L=2,R=5: 1+6=7
    # L=3,R=4: 2+4=6 yes
    # L=4,R=3: 4+2=6 yes
    # L=5,R=2: 6+1=7
    # L=6,R=1: 8+0=8
    # L=7,R=0: 10+0=10
    # So L=3,4 (range size 2).
    #
    # The range size seems to be at most 3? Let's check k=9: S(9)=? h=3, full=7, last=2. S(9)=0+2+8+6=16. S(9)-8=8.
    # L=0,R=8: 0+13=13
    # L=1,R=7: 0+10=10
    # L=2,R=6: 1+8=9
    # L=3,R=5: 2+6=8 yes
    # L=4,R=4: 4+4=8 yes
    # L=5,R=3: 6+2=8 yes
    # L=6,R=2: 8+1=9
    # L=7,R=1: 10+0=10
    # L=8,R=0: 13+0=13
    # So L=3,4,5 (range size 3).
    # k=10: S(10)=? h=3, full=7, last=3. S(10)=0+2+8+9=19. S(10)-9=10.
    # L=0,R=9: 0+16=16
    # L=1,R=8: 0+13=13
    # L=2,R=7: 1+10=11
    # L=3,R=6: 2+8=10 yes
    # L=4,R=5: 4+6=10 yes
    # L=5,R=4: 6+4=10 yes
    # L=6,R=3: 8+2=10 yes
    # L=7,R=2: 10+1=11
    # L=8,R=1: 13+0=13
    # L=9,R=0: 16+0=16
    # So L=3,4,5,6 (range size 4).
    # k=11: S(11)=? h=3, full=7, last=4. S(11)=0+2+8+12=22. S(11)-10=12.
    # L=0,R=10: 0+19=19
    # L=1,R=9: 0+16=16
    # L=2,R=8: 1+13=14
    # L=3,R=7: 2+10=12 yes
    # L=4,R=6: 4+8=12 yes
    # L=5,R=5: 6+6=12 yes
    # L=6,R=4: 8+4=12 yes
    # L=7,R=3: 10+2=12 yes
    # L=8,R=2: 13+1=14
    # L=9,R=1: 16+0=16
    # L=10,R=0: 19+0=19
    # So L=3,4,5,6,7 (range size 5).
    # k=12: S(12)=? h=3, full=7, last=5. S(12)=0+2+8+15=25. S(12)-11=14.
    # L=0,R=11: 0+22=22
    # L=1,R=10: 0+19=19
    # L=2,R=9: 1+16=17
    # L=3,R=8: 2+13=15
    # L=4,R=7: 4+10=14 yes
    # L=5,R=6: 6+8=14 yes
    # L=6,R=5: 8+6=14 yes
    # L=7,R=4: 10+4=14 yes
    # L=8,R=3: 13+2=15
    # L=9,R=2: 16+1=17
    # L=10,R=1: 19+0=19
    # L=11,R=0: 22+0=22
    # So L=4,5,6,7 (range size 4).
    # k=13: S(13)=? h=3, full=7, last=6. S(13)=0+2+8+18=28. S(13)-12=16.
    # L=0,R=12: 0+25=25
    # L=1,R=11: 0+22=22
    # L=2,R=10: 1+19=20
    # L=3,R=9: 2+16=18
    # L=4,R=8: 4+13=17
    # L=5,R=7: 6+10=16 yes
    # L=6,R=6: 8+8=16 yes
    # L=7,R=5: 10+6=16 yes
    # L=8,R=4: 13+4=17
    # L=9,R=3: 16+2=18
    # L=10,R=2: 19+1=20
    # L=11,R=1: 22+0=22
    # L=12,R=0: 25+0=25
    # So L=5,6,7 (range size 3).
    # k=14: S(14)=? h=3, full=7, last=7. S(14)=0+2+8+21=31. S(14)-13=18.
    # L=0,R=13: 0+28=28
    # L=1,R=12: 0+25=25
    # L=2,R=11: 1+22=23
    # L=3,R=10: 2+19=21
    # L=4,R=9: 4+16=20
    # L=5,R=8: 6+13=19
    # L=6,R=7: 8+10=18 yes
    # L=7,R=6: 10+8=18 yes
    # L=8,R=5: 13+6=19
    # L=9,R=4: 16+4=20
    # L=10,R=3: 19+2=21
    # L=11,R=2: 22+1=23
    # L=12,R=1: 25+0=25
    # L=13,R=0: 28+0=28
    # So L=6,7 (range size 2).
    # k=15: S(15)=? h=3, full=7, last=8. S(15)=0+2+8+24=34. S(15)-14=20.
    # L=0,R=14: 0+31=31
    # L=1,R=13: 0+28=28
    # L=2,R=12: 1+25=26
    # L=3,R=11: 2+22=24
    # L=4,R=10: 4+19=23
    # L=5,R=9: 6+16=22
    # L=6,R=8: 8+13=21
    # L=7,R=7: 10+10=20 yes
    # L=8,R=6: 13+8=21
    # L=9,R=5: 16+6=22
    # L=10,R=4: 19+4=23
    # L=11,R=3: 22+2=24
    # L=12,R=2: 25+1=26
    # L=13,R=1: 28+0=28
    # L=14,R=0: 31+0=31
    # So L=7 only (range size 1).
    #
    # The range size can be up to about h? For k=2^h-1, range size 1. For k=2^h, range size 2.
    # For k=2^h + something, range size can be larger. In general, the range size is at most
    # the number of nodes in the last level? Actually, for k=2^h + 2^{h-1} - 1, range size is 2^{h-1}?
    # Let's check k=11 (h=3, 2^3=8, 2^{2}=4, 8+4-1=11). Range size 5 = 2^{h-1}+1? 4+1=5.
    # k=12: range size 4 = 2^{h-1}. k=13: range size 3. k=14: range size 2. k=15: range size 1.
    # So the range size can be up to 2^{h-1}+1, which for n=1e6, h=19, 2^{18}=262144. That's too large
    # to iterate over for each k. We need a better way.
    #
    # But wait, we need to compute dp[k][p][q] = sum over L in optimal range of
    # (sum_{qL != r} dp[L][p][qL]) * (sum_{qR == r} dp[R][pR][qR]).
    # This is a convolution-like sum over L. If the range is large, we need to compute it efficiently.
    #
    # However, note that the optimal L range is contiguous. We can precompute prefix sums
    # of dp[L][p][qL] for each p and qL, and similarly for R. But R = k-1-L, so as L varies,
    # R varies in the opposite direction. We can use prefix sums over L for the left part,
    # and suffix sums for the right part? But the right part depends on pR = (p+L+1) mod 2,
    # which depends on L parity. So we need to split by parity of L.
    #
    # Let's define for each k, p, q:
    # dp[k][p][q] = number of valid striped BSTs with k nodes, starting parity p, root parity q.
    #
    # For k=0: dp[0][p][q] = 0 for all p,q (empty tree has no root).
    # For k=1: dp[1][p][q] = 1 if q == p else 0. (single node, root parity = starting parity)
    #
    # For k>=2:
    # For each optimal L (0 <= L <= k-1), R = k-1-L.
    # r = (p + L) mod 2.
    # Left subtree: size L, starting parity p. We need sum over qL != r of dp[L][p][qL].
    # Right subtree: size R, starting parity pR = (p + L + 1) mod 2. We need sum over qR == r of dp[R][pR][qR].
    # Contribution = left_sum * right_sum.
    # dp[k][p][r] += contribution.
    #
    # Note that for a given k and p, r is determined by L parity: r = (p + L) mod 2.
    # So for L even, r = p; for L odd, r = 1-p.
    # Thus we can split the sum over L into even L and odd L.
    #
    # For even L: r = p. Left sum = sum_{qL != p} dp[L][p][qL] = total[L][p] - dp[L][p][p].
    # Right: pR = (p + L + 1) mod 2 = (p + 1) mod 2 = 1-p (since L even).
    # Right sum = sum_{qR == p} dp[R][1-p][qR] = dp[R][1-p][p].
    #
    # For odd L: r = 1-p. Left sum = total[L][p] - dp[L][p][1-p].
    # Right: pR = (p + L + 1) mod 2 = (p + 1 + 1) mod 2 = p (since L odd).
    # Right sum = sum_{qR == 1-p} dp[R][p][qR] = dp[R][p][1-p].
    #
    # So dp[k][p][p] = sum_{L even, optimal} (total[L][p] - dp[L][p][p]) * dp[R][1-p][p]
    # dp[k][p][1-p] = sum_{L odd, optimal} (total[L][p] - dp[L][p][1-p]) * dp[R][p][1-p]
    #
    # where total[L][p] = dp[L][p][0] + dp[L][p][1].
    #
    # Now, the optimal L range is contiguous. We need to sum over L in [L_min, L_max] with
    # L even or odd. We can precompute prefix sums over L for each p and q of dp[L][p][q]
    # and total[L][p]. But R = k-1-L, so the right factor depends on R, which is not a simple
    # prefix sum because it's evaluated at R = k-1-L. However, we can rewrite the sum as
    # sum over L of f(L) * g(k-1-L). This is a convolution. But since we only need it for
    # specific k, and the range of L is contiguous, we can compute it by iterating over L
    # if the range is small. But the range can be large (up to 2^{h-1}).
    #
    # Wait, is the range really that large? Let's check k=11: range size 5. k=2^h + 2^{h-1} - 1
    # gives range size 2^{h-1}+1. For h=19, that's 262145. For n=1e6, h=19, 2