import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    h = int(input_data[1])
    a = list(map(int, input_data[2:2+n]))
    
    MOD = 1000000007
    
    # We need to add (h - a[i]) to each position.
    # Let d[i] = h - a[i]. If any d[i] < 0, impossible.
    # We perform operations: each operation is a segment [l, r], adding 1.
    # Constraint: no two segments share the same l, and no two share the same r.
    # This means each index can be the left endpoint of at most one segment,
    # and the right endpoint of at most one segment.
    # We need to cover each position i exactly d[i] times.
    # Think of it as: at each position, we have some active segments covering it.
    # The number of active segments at position i must equal d[i].
    # When moving from i to i+1:
    #   - Some segments may end at i (right endpoint = i)
    #   - Some segments may start at i+1 (left endpoint = i+1)
    # Since each index can be left endpoint at most once, at most one segment starts at i+1.
    # Similarly, at most one segment ends at i.
    # So the change in active count from i to i+1 is:
    #   active[i+1] = active[i] - (1 if a segment ends at i else 0) + (1 if a segment starts at i+1 else 0)
    # But we don't know which segments end/start. However, the number of ways to choose
    # which active segments end at i and whether a new one starts at i+1 depends on active count.
    
    # Let's formalize:
    # Let d[i] = h - a[i]. We need active[i] = d[i] for all i.
    # At position i, we have d[i] active segments.
    # Moving to i+1:
    #   We can end some number of segments at i. Let e_i = number of segments ending at i.
    #   Since each index can be right endpoint at most once, e_i ∈ {0, 1}.
    #   Similarly, start at i+1: s_{i+1} ∈ {0, 1}.
    #   Then d[i+1] = d[i] - e_i + s_{i+1}.
    # So e_i - s_{i+1} = d[i] - d[i+1].
    # Let diff = d[i] - d[i+1].
    # Possible cases:
    #   If diff == 0: e_i = s_{i+1}. Since both in {0,1}, either both 0 or both 1.
    #       If both 0: no segment ends at i, no segment starts at i+1.
    #           Number of ways: 1 (do nothing).
    #       If both 1: one segment ends at i, one starts at i+1.
    #           Number of ways: choose which active segment ends at i: d[i] choices.
    #           Then the new segment starts at i+1 (only 1 way to start, since left endpoint is fixed to i+1).
    #           So d[i] ways.
    #       Total ways for diff=0: 1 + d[i].
    #   If diff == 1: e_i - s_{i+1} = 1 => e_i=1, s_{i+1}=0.
    #       One segment ends at i, no new segment starts.
    #       Number of ways: choose which active segment ends: d[i] choices.
    #   If diff == -1: e_i=0, s_{i+1}=1.
    #       No segment ends, one new segment starts at i+1.
    #       Number of ways: 1 (just start new segment).
    #   If |diff| > 1: impossible (0 ways).
    # Also need to handle boundaries:
    #   Before position 1: d[0] = 0 (no active segments).
    #   At position 1: we need d[1] active segments. Since no segments can end before 1,
    #   we must start d[1] segments at position 1? But each index can be left endpoint at most once,
    #   so we can start at most 1 segment at position 1. Thus d[1] must be 0 or 1.
    #   Actually, wait: segments can start at position 1 only once (since l=1 at most once).
    #   So d[1] can be at most 1? But example: n=3, h=2, a=[1,1,1] => d=[1,1,1].
    #   d[1]=1, so we start 1 segment at position 1. That's fine.
    #   What if d[1] > 1? Then impossible because we can only start one segment at position 1.
    #   But wait: could segments start before position 1? No, indices start at 1.
    #   So indeed d[1] must be 0 or 1.
    #   Similarly, after position n: d[n+1] = 0. At position n, we must end all active segments.
    #   Since each index can be right endpoint at most once, we can end at most 1 segment at position n.
    #   So d[n] must be 0 or 1? Let's check: if d[n] > 1, we need to end d[n] segments at n,
    #   but only 1 allowed. So impossible.
    #   Actually, we can end segments at n only once, so d[n] <= 1.
    #   But wait: what if d[n] = 2? Then we have 2 active segments at n, we need to end both at n,
    #   but only one can end at n. So impossible.
    #   So d[1] <= 1 and d[n] <= 1.
    #   Also, for i from 1 to n-1, we have transitions.
    #   Let's check example 1: n=3, h=2, a=[1,1,1] => d=[1,1,1].
    #   d[1]=1 (ok). d[3]=1 (ok).
    #   i=1: d[1]=1, d[2]=1 => diff=0 => ways = 1 + d[1] = 2.
    #   i=2: d[2]=1, d[3]=1 => diff=0 => ways = 1 + d[2] = 2.
    #   Total ways = 2 * 2 = 4. Matches example output 4.
    #   Example 2: n=5, h=1, a=[1,1,1,1,1] => d=[0,0,0,0,0].
    #   d[1]=0, d[5]=0.
    #   For each i: diff=0, d[i]=0 => ways = 1+0=1. Total 1. Matches.
    #   Example 3: n=4, h=3, a=[3,2,1,1] => d=[0,1,2,2].
    #   d[1]=0 ok. d[4]=2 > 1 => impossible => 0. Matches.
    
    # So algorithm:
    # Compute d[i] = h - a[i]. If any d[i] < 0 => 0.
    # If d[0] > 1 or d[n-1] > 1 => 0.
    # ans = 1
    # For i from 0 to n-2:
    #   diff = d[i] - d[i+1]
    #   if diff == 0:
    #       ans = ans * (1 + d[i]) % MOD
    #   elif diff == 1:
    #       ans = ans * d[i] % MOD
    #   elif diff == -1:
    #       ans = ans * 1 % MOD
    #   else:
    #       ans = 0; break
    # Also need to check d[0] <= 1 and d[n-1] <= 1.
    # But wait: what about d[0]? d[0] is active before position 1, which is 0.
    # Actually, we defined d[i] for i=1..n. Let's use 0-indexed array d[0..n-1] for positions 1..n.
    # Before position 1, active = 0. So we need to start d[0] segments at position 1.
    # Since at most 1 segment can start at position 1, d[0] must be 0 or 1.
    # Similarly, after position n, active = 0. So we need to end d[n-1] segments at position n.
    # Since at most 1 segment can end at position n, d[n-1] must be 0 or 1.
    # Also, for i from 0 to n-2, we have transition from d[i] to d[i+1].
    # But wait: the transition formula assumed we have d[i] active at position i, and we move to i+1.
    # The number of ways to choose which segments end at i is based on d[i] active segments.
    # But we also need to consider that at position i, we might have started some segments at i.
    # Actually, the active count at position i is exactly d[i]. The segments that are active at i
    # are those that started at some j <= i and haven't ended yet.
    # When moving from i to i+1, we can end some of the d[i] active segments at i.
    # The number of ways to choose which ones end is C(d[i], e_i) if e_i is the number ending.
    # Since e_i ∈ {0,1}, C(d[i],0)=1, C(d[i],1)=d[i].
    # Then we start s_{i+1} new segments at i+1. Since at most 1 can start, s_{i+1} ∈ {0,1}.
    # The new segment is just one specific segment (the one starting at i+1), so 1 way.
    # So the number of ways for the transition is C(d[i], e_i) * 1.
    # And we need d[i+1] = d[i] - e_i + s_{i+1}.
    # So the cases are exactly as above.
    # But we also need to ensure that the total number of segments started at each position is at most 1.
    # Our transition ensures s_{i+1} ∈ {0,1}, so that's fine.
    # Similarly, e_i ∈ {0,1} ensures at most one ends at i.
    # So the only additional constraints are d[0] <= 1 and d[n-1] <= 1.
    # Wait: what about d[0]? At position 1, we start s_1 segments. But s_1 is not covered by the transition
    # from i=0 to i=1 because there is no position 0. We need to handle the start at position 1 separately.
    # Actually, we can think of a virtual position 0 with d[0] = 0 (active before position 1).
    # Then transition from 0 to 1: d[1] = d[0] - e_0 + s_1 = 0 - 0 + s_1 = s_1.
    # Since s_1 ∈ {0,1}, d[1] must be 0 or 1. And e_0 = 0 (no segments end at position 0).
    # So the number of ways for this transition is 1 (since e_0=0, s_1=d[1], and if d[1]=1, we start 1 segment, 1 way).
    # So we can just check d[0] <= 1 (using 0-indexed d for positions 1..n).
    # Similarly, after position n, we have virtual position n+1 with d[n+1] = 0.
    # Transition from n to n+1: d[n+1] = d[n] - e_n + s_{n+1} = d[n] - e_n + 0 = 0 => e_n = d[n].
    # Since e_n ∈ {0,1}, d[n] must be 0 or 1. And number of ways is C(d[n], e_n) = C(d[n], d[n]) = 1.
    # So we just need d[n-1] <= 1.
    # So the algorithm is correct.
    
    d = [h - x for x in a]
    for x in d:
        if x < 0:
            print(0)
            return
    if d[0] > 1 or d[-1] > 1:
        print(0)
        return
    ans = 1
    for i in range(n-1):
        diff = d[i] - d[i+1]
        if diff == 0:
            ans = ans * (1 + d[i]) % MOD
        elif diff == 1:
            ans = ans * d[i] % MOD
        elif diff == -1:
            # ans = ans * 1 % MOD
            pass
        else:
            print(0)
            return
    print(ans % MOD)

if __name__ == "__main__":
    solve()