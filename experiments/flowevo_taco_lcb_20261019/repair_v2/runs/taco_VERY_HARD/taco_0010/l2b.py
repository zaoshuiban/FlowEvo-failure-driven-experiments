import sys
from bisect import bisect_left, bisect_right


class ActiveSet:
    __slots__ = ("n", "bit", "event", "total")

    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)
        self.event = [-1] * n
        self.total = 0

    def _add(self, idx, delta):
        n = self.n
        bit = self.bit
        idx += 1
        while idx <= n:
            bit[idx] += delta
            idx += idx & -idx

    def _prefix(self, k):
        # sum on indices [0, k)
        bit = self.bit
        res = 0
        while k > 0:
            res += bit[k]
            k -= k & -k
        return res

    def kth(self, k):
        # 1-indexed k-th active position, returns 0-based index
        n = self.n
        bit = self.bit
        idx = 0
        bitmask = 1 << (n.bit_length() - 1)

        while bitmask:
            nxt = idx + bitmask
            if nxt <= n and bit[nxt] < k:
                idx = nxt
                k -= bit[nxt]
            bitmask >>= 1

        return idx

    def query_idx(self, left, right):
        if left > right:
            return -1

        before = self._prefix(left)
        after = self._prefix(right + 1)

        if before == after:
            return -1

        idx = self.kth(before + 1)
        return self.event[idx]

    def filter_idx(self, left, right):
        while self.total > 0:
            idx = self.kth(1)
            if idx < left:
                self.remove_idx(idx)
            else:
                break

        while self.total > 0:
            idx = self.kth(self.total)
            if idx > right:
                self.remove_idx(idx)
            else:
                break

    def clear(self):
        while self.total > 0:
            idx = self.kth(1)
            self.remove_idx(idx)

    def insert(self, idx, event_id):
        if self.event[idx] == -1:
            self._add(idx, 1)
            self.total += 1
        self.event[idx] = event_id

    def remove_idx(self, idx):
        if self.event[idx] != -1:
            self._add(idx, -1)
            self.total -= 1
            self.event[idx] = -1

    def any_event(self):
        idx = self.kth(1)
        return self.event[idx]


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    _m = next(it)

    queries = []
    ks = []

    for _ in range(n):
        k = next(it)
        al = next(it)
        bl = next(it)
        ar = next(it)
        br = next(it)
        queries.append((k, al, bl, ar, br))
        ks.append(k)

    values = sorted(set([0] + ks))
    val_to_idx = {v: i for i, v in enumerate(values)}
    size = len(values)

    event_type = []
    event_time = []
    event_parent = []

    def add_event(typ, tm, parent):
        event_type.append(typ)
        event_time.append(tm)
        event_parent.append(parent)
        return len(event_type) - 1

    # type 0 = left card value, type 1 = right card value
    initial_left = add_event(0, 0, -1)
    initial_right = add_event(1, 0, -1)

    left_set = ActiveSet(size)
    right_set = ActiveSet(size)

    zero_idx = val_to_idx[0]
    left_set.insert(zero_idx, initial_left)
    right_set.insert(zero_idx, initial_right)

    for i, (k, al, bl, ar, br) in enumerate(queries, 1):
        k_idx = val_to_idx[k]

        l_low = bisect_left(values, al)
        l_high = bisect_right(values, bl) - 1

        r_low = bisect_left(values, ar)
        r_high = bisect_right(values, br) - 1

        k_in_left = al <= k <= bl
        k_in_right = ar <= k <= br

        parent_for_left = -1
        if k_in_left:
            parent_for_left = right_set.query_idx(r_low, r_high)

        parent_for_right = -1
        if k_in_right:
            parent_for_right = left_set.query_idx(l_low, l_high)

        can_replace_left = parent_for_left != -1
        can_replace_right = parent_for_right != -1

        # Update possible left-card values.
        if can_replace_right:
            left_set.filter_idx(l_low, l_high)
        else:
            left_set.clear()

        if can_replace_left:
            ev = add_event(0, i, parent_for_left)
            left_set.insert(k_idx, ev)

        # Update possible right-card values.
        if can_replace_left:
            right_set.filter_idx(r_low, r_high)
        else:
            right_set.clear()

        if can_replace_right:
            ev = add_event(1, i, parent_for_right)
            right_set.insert(k_idx, ev)

    if left_set.total == 0 and right_set.total == 0:
        print("No")
        return

    if left_set.total > 0:
        final_event = left_set.any_event()
    else:
        final_event = right_set.any_event()

    answer = [0] * (n + 2)

    cur = final_event
    end_time = n

    while event_time[cur] > 0:
        t = event_time[cur]
        typ = event_type[cur]

        if typ == 0:
            # Replace left at time t, then keep the left card unchanged.
            answer[t] = 0
            fill_value = 1
        else:
            # Replace right at time t, then keep the right card unchanged.
            answer[t] = 1
            fill_value = 0

        for pos in range(t + 1, end_time + 1):
            answer[pos] = fill_value

        cur = event_parent[cur]
        end_time = t - 1

    # Initial event at time 0.
    if event_type[cur] == 0:
        fill_value = 1
    else:
        fill_value = 0

    for pos in range(1, end_time + 1):
        answer[pos] = fill_value

    print("Yes")
    print(" ".join(str(answer[i]) for i in range(1, n + 1)))


if __name__ == "__main__":
    solve()