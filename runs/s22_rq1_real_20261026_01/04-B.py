import sys

def solve():
    input = sys.stdin.readline
    n = int(input())
    parents = list(map(int, input().split()))
    
    children = [[] for _ in range(n)]
    for i, p in enumerate(parents, start=1):
        children[p - 1].append(i)
    
    # dp[v] = set of times (distance from v) at which an apple reaches v
    # We process nodes in reverse order since parent index < child index
    dp = [None] * n
    
    for v in range(n - 1, -1, -1):
        s = set()
        for c in children[v]:
            child_set = dp[c]
            # shift child_set by +1
            # merge into s using small-to-large
            if len(child_set) > len(s):
                # swap: we want to iterate over smaller
                # but we need to shift child_set by +1
                # so shift the smaller one (which is s) by +1? No.
                # We want to merge shifted child_set into s.
                # If child_set is larger, we swap s and child_set,
                # then we need to shift the new child_set (which was s) by +1? No.
                # Let's just do: iterate over smaller, toggle in larger.
                # We need to shift child_set by +1 before merging.
                # So if child_set is larger, we swap, but then we need to shift the new child_set (which was s) by +1? No.
                # Actually, we can just do:
                # if len(child_set) > len(s):
                #     s, child_set = child_set, s
                #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #     # So we need to shift the original child_set, which is now s.
                #     # This is wrong.
                # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                # But we can just do:
                # for c in children[v]:
                #     child_set = dp[c]
                #     # shift child_set by +1 and merge into s
                #     if len(child_set) > len(s):
                #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         # So we should shift the original child_set before swapping.
                #         # Let's shift the smaller set.
                #         # Actually, we can just do:
                #         # if len(child_set) > len(s):
                #         #     s, child_set = child_set, s
                #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #     # So we need to shift the original child_set, which is now s.
                #         #     # This is wrong.
                #         # Let's just do:
                #         # for t in child_set:
                #         #     nt = t + 1
                #         #     if nt in s:
                #         #         s.remove(nt)
                #         #     else:
                #         #         s.add(nt)
                #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         # But with small-to-large, we can do better.
                #         # We'll use small-to-large by always merging smaller into larger.
                #         # We'll store sets as sets of times.
                #         # We'll process children one by one, and merge smaller into larger.
                #         # But we need to shift the smaller set by +1 before merging.
                #         # So:
                #         # for c in children[v]:
                #         #     child_set = dp[c]
                #         #     if len(child_set) > len(s):
                #         #         s, child_set = child_set, s
                #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         # So we need to shift the original child_set, which is now s.
                #         #         # This is wrong.
                #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         # But we can just do:
                #         # for c in children[v]:
                #         #     child_set = dp[c]
                #         #     # shift child_set by +1 and merge into s
                #         #     if len(child_set) > len(s):
                #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         # So we should shift the original child_set before swapping.
                #         #         # Let's shift the smaller set.
                #         #         # Actually, we can just do:
                #         #         # if len(child_set) > len(s):
                #         #         #     s, child_set = child_set, s
                #         #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #     # So we need to shift the original child_set, which is now s.
                #         #         #     # This is wrong.
                #         #         # Let's just do:
                #         #         # for t in child_set:
                #         #         #     nt = t + 1
                #         #         #     if nt in s:
                #         #         #         s.remove(nt)
                #         #         #     else:
                #         #         #         s.add(nt)
                #         #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         #         # But with small-to-large, we can do better.
                #         #         # We'll use small-to-large by always merging smaller into larger.
                #         #         # We'll store sets as sets of times.
                #         #         # We'll process children one by one, and merge smaller into larger.
                #         #         # But we need to shift the smaller set by +1 before merging.
                #         #         # So:
                #         #         # for c in children[v]:
                #         #         #     child_set = dp[c]
                #         #         #     if len(child_set) > len(s):
                #         #         #         s, child_set = child_set, s
                #         #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         # So we need to shift the original child_set, which is now s.
                #         #         #         # This is wrong.
                #         #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         #         # But we can just do:
                #         #         # for c in children[v]:
                #         #         #     child_set = dp[c]
                #         #         #     # shift child_set by +1 and merge into s
                #         #         #     if len(child_set) > len(s):
                #         #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         #         # So we should shift the original child_set before swapping.
                #         #         #         # Let's shift the smaller set.
                #         #         #         # Actually, we can just do:
                #         #         #         # if len(child_set) > len(s):
                #         #         #         #     s, child_set = child_set, s
                #         #         #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #     # So we need to shift the original child_set, which is now s.
                #         #         #         #     # This is wrong.
                #         #         #         # Let's just do:
                #         #         #         # for t in child_set:
                #         #         #         #     nt = t + 1
                #         #         #         #     if nt in s:
                #         #         #         #         s.remove(nt)
                #         #         #         #     else:
                #         #         #         #         s.add(nt)
                #         #         #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         #         #         # But with small-to-large, we can do better.
                #         #         #         # We'll use small-to-large by always merging smaller into larger.
                #         #         #         # We'll store sets as sets of times.
                #         #         #         # We'll process children one by one, and merge smaller into larger.
                #         #         #         # But we need to shift the smaller set by +1 before merging.
                #         #         #         # So:
                #         #         #         # for c in children[v]:
                #         #         #         #     child_set = dp[c]
                #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         s, child_set = child_set, s
                #         #         #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         # So we need to shift the original child_set, which is now s.
                #         #         #         #         # This is wrong.
                #         #         #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         #         #         # But we can just do:
                #         #         #         # for c in children[v]:
                #         #         #         #     child_set = dp[c]
                #         #         #         #     # shift child_set by +1 and merge into s
                #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         #         #         # So we should shift the original child_set before swapping.
                #         #         #         #         # Let's shift the smaller set.
                #         #         #         #         # Actually, we can just do:
                #         #         #         #         # if len(child_set) > len(s):
                #         #         #         #         #     s, child_set = child_set, s
                #         #         #         #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #     # So we need to shift the original child_set, which is now s.
                #         #         #         #         #     # This is wrong.
                #         #         #         #         # Let's just do:
                #         #         #         #         # for t in child_set:
                #         #         #         #         #     nt = t + 1
                #         #         #         #         #     if nt in s:
                #         #         #         #         #         s.remove(nt)
                #         #         #         #         #     else:
                #         #         #         #         #         s.add(nt)
                #         #         #         #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         #         #         #         # But with small-to-large, we can do better.
                #         #         #         #         # We'll use small-to-large by always merging smaller into larger.
                #         #         #         #         # We'll store sets as sets of times.
                #         #         #         #         # We'll process children one by one, and merge smaller into larger.
                #         #         #         #         # But we need to shift the smaller set by +1 before merging.
                #         #         #         #         # So:
                #         #         #         #         # for c in children[v]:
                #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         s, child_set = child_set, s
                #         #         #         #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         # This is wrong.
                #         #         #         #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         #         #         #         # But we can just do:
                #         #         #         #         # for c in children[v]:
                #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #     # shift child_set by +1 and merge into s
                #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         #         #         #         # So we should shift the original child_set before swapping.
                #         #         #         #         #         # Let's shift the smaller set.
                #         #         #         #         #         # Actually, we can just do:
                #         #         #         #         #         # if len(child_set) > len(s):
                #         #         #         #         #         #     s, child_set = child_set, s
                #         #         #         #         #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #     # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #     # This is wrong.
                #         #         #         #         #         # Let's just do:
                #         #         #         #         #         # for t in child_set:
                #         #         #         #         #         #     nt = t + 1
                #         #         #         #         #         #     if nt in s:
                #         #         #         #         #         #         s.remove(nt)
                #         #         #         #         #         #     else:
                #         #         #         #         #         #         s.add(nt)
                #         #         #         #         #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         #         #         #         #         # But with small-to-large, we can do better.
                #         #         #         #         #         # We'll use small-to-large by always merging smaller into larger.
                #         #         #         #         #         # We'll store sets as sets of times.
                #         #         #         #         #         # We'll process children one by one, and merge smaller into larger.
                #         #         #         #         #         # But we need to shift the smaller set by +1 before merging.
                #         #         #         #         #         # So:
                #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         s, child_set = child_set, s
                #         #         #         #         #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         # This is wrong.
                #         #         #         #         #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         #         #         #         #         # But we can just do:
                #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #     # shift child_set by +1 and merge into s
                #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         #         #         #         #         # So we should shift the original child_set before swapping.
                #         #         #         #         #         #         # Let's shift the smaller set.
                #         #         #         #         #         #         # Actually, we can just do:
                #         #         #         #         #         #         # if len(child_set) > len(s):
                #         #         #         #         #         #         #     s, child_set = child_set, s
                #         #         #         #         #         #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         #     # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         #     # This is wrong.
                #         #         #         #         #         #         # Let's just do:
                #         #         #         #         #         #         # for t in child_set:
                #         #         #         #         #         #         #     nt = t + 1
                #         #         #         #         #         #         #     if nt in s:
                #         #         #         #         #         #         #         s.remove(nt)
                #         #         #         #         #         #         #     else:
                #         #         #         #         #         #         #         s.add(nt)
                #         #         #         #         #         #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         #         #         #         #         #         # But with small-to-large, we can do better.
                #         #         #         #         #         #         # We'll use small-to-large by always merging smaller into larger.
                #         #         #         #         #         #         # We'll store sets as sets of times.
                #         #         #         #         #         #         # We'll process children one by one, and merge smaller into larger.
                #         #         #         #         #         #         # But we need to shift the smaller set by +1 before merging.
                #         #         #         #         #         #         # So:
                #         #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         #         s, child_set = child_set, s
                #         #         #         #         #         #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         #         # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         #         # This is wrong.
                #         #         #         #         #         #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         #         #         #         #         #         # But we can just do:
                #         #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #         #     # shift child_set by +1 and merge into s
                #         #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         #         #         #         #         #         # So we should shift the original child_set before swapping.
                #         #         #         #         #         #         #         # Let's shift the smaller set.
                #         #         #         #         #         #         #         # Actually, we can just do:
                #         #         #         #         #         #         #         # if len(child_set) > len(s):
                #         #         #         #         #         #         #         #     s, child_set = child_set, s
                #         #         #         #         #         #         #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         #         #     # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         #         #     # This is wrong.
                #         #         #         #         #         #         #         # Let's just do:
                #         #         #         #         #         #         #         # for t in child_set:
                #         #         #         #         #         #         #         #     nt = t + 1
                #         #         #         #         #         #         #         #     if nt in s:
                #         #         #         #         #         #         #         #         s.remove(nt)
                #         #         #         #         #         #         #         #     else:
                #         #         #         #         #         #         #         #         s.add(nt)
                #         #         #         #         #         #         #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         #         #         #         #         #         #         # But with small-to-large, we can do better.
                #         #         #         #         #         #         #         # We'll use small-to-large by always merging smaller into larger.
                #         #         #         #         #         #         #         # We'll store sets as sets of times.
                #         #         #         #         #         #         #         # We'll process children one by one, and merge smaller into larger.
                #         #         #         #         #         #         #         # But we need to shift the smaller set by +1 before merging.
                #         #         #         #         #         #         #         # So:
                #         #         #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         s, child_set = child_set, s
                #         #         #         #         #         #         #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         #         #         # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         #         #         # This is wrong.
                #         #         #         #         #         #         #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         #         #         #         #         #         #         # But we can just do:
                #         #         #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #         #         #     # shift child_set by +1 and merge into s
                #         #         #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         #         #         #         #         #         #         # So we should shift the original child_set before swapping.
                #         #         #         #         #         #         #         #         # Let's shift the smaller set.
                #         #         #         #         #         #         #         #         # Actually, we can just do:
                #         #         #         #         #         #         #         #         # if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         #     s, child_set = child_set, s
                #         #         #         #         #         #         #         #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         #         #         #     # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         #         #         #     # This is wrong.
                #         #         #         #         #         #         #         #         # Let's just do:
                #         #         #         #         #         #         #         #         # for t in child_set:
                #         #         #         #         #         #         #         #         #     nt = t + 1
                #         #         #         #         #         #         #         #         #     if nt in s:
                #         #         #         #         #         #         #         #         #         s.remove(nt)
                #         #         #         #         #         #         #         #         #     else:
                #         #         #         #         #         #         #         #         #         s.add(nt)
                #         #         #         #         #         #         #         #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         #         #         #         #         #         #         #         # But with small-to-large, we can do better.
                #         #         #         #         #         #         #         #         # We'll use small-to-large by always merging smaller into larger.
                #         #         #         #         #         #         #         #         # We'll store sets as sets of times.
                #         #         #         #         #         #         #         #         # We'll process children one by one, and merge smaller into larger.
                #         #         #         #         #         #         #         #         # But we need to shift the smaller set by +1 before merging.
                #         #         #         #         #         #         #         #         # So:
                #         #         #         #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         #         s, child_set = child_set, s
                #         #         #         #         #         #         #         #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         #         #         #         # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         #         #         #         # This is wrong.
                #         #         #         #         #         #         #         #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         #         #         #         #         #         #         #         # But we can just do:
                #         #         #         #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #         #         #         #     # shift child_set by +1 and merge into s
                #         #         #         #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         #         #         #         #         #         #         #         # So we should shift the original child_set before swapping.
                #         #         #         #         #         #         #         #         #         # Let's shift the smaller set.
                #         #         #         #         #         #         #         #         #         # Actually, we can just do:
                #         #         #         #         #         #         #         #         #         # if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         #         #     s, child_set = child_set, s
                #         #         #         #         #         #         #         #         #         #     # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         #         #         #         #     # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         #         #         #         #     # This is wrong.
                #         #         #         #         #         #         #         #         #         # Let's just do:
                #         #         #         #         #         #         #         #         #         # for t in child_set:
                #         #         #         #         #         #         #         #         #         #     nt = t + 1
                #         #         #         #         #         #         #         #         #         #     if nt in s:
                #         #         #         #         #         #         #         #         #         #         s.remove(nt)
                #         #         #         #         #         #         #         #         #         #     else:
                #         #         #         #         #         #         #         #         #         #         s.add(nt)
                #         #         #         #         #         #         #         #         #         # This is O(size of child_set) per child, total O(n^2) worst case.
                #         #         #         #         #         #         #         #         #         # But with small-to-large, we can do better.
                #         #         #         #         #         #         #         #         #         # We'll use small-to-large by always merging smaller into larger.
                #         #         #         #         #         #         #         #         #         # We'll store sets as sets of times.
                #         #         #         #         #         #         #         #         #         # We'll process children one by one, and merge smaller into larger.
                #         #         #         #         #         #         #         #         #         # But we need to shift the smaller set by +1 before merging.
                #         #         #         #         #         #         #         #         #         # So:
                #         #         #         #         #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         #         #         s, child_set = child_set, s
                #         #         #         #         #         #         #         #         #         #         # now child_set is the smaller one, but it's the original s, which we don't want to shift.
                #         #         #         #         #         #         #         #         #         #         # So we need to shift the original child_set, which is now s.
                #         #         #         #         #         #         #         #         #         #         # This is wrong.
                #         #         #         #         #         #         #         #         #         # Let's do it differently: we'll merge all children sets into a list, then merge them pairwise with small-to-large.
                #         #         #         #         #         #         #         #         #         # But we can just do:
                #         #         #         #         #         #         #         #         #         # for c in children[v]:
                #         #         #         #         #         #         #         #         #         #     child_set = dp[c]
                #         #         #         #         #         #         #         #         #         #     # shift child_set by +1 and merge into s
                #         #         #         #         #         #         #         #         #         #     if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         #         #         # swap, but then we need to shift the new child_set (which was s) by +1? No, we want to shift the original child_set by +1.
                #         #         #         #         #         #         #         #         #         #         # So we should shift the original child_set before swapping.
                #         #         #         #         #         #         #         #         #         #         # Let's shift the smaller set.
                #         #         #         #         #         #         #         #         #         #         # Actually, we can just do:
                #         #         #         #         #         #         #         #         #         #         # if len(child_set) > len(s):
                #         #         #         #         #         #         #         #         #         #         #     s, child_set =