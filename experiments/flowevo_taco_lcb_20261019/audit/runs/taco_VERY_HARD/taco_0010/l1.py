import sys

sys.setrecursionlimit(1_000_000)


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    max_nodes = 2 * n + 20

    left = [0] * max_nodes
    right = [0] * max_nodes
    keys = [0] * max_nodes
    priority = [0] * max_nodes

    ptr = 0
    seed = 0x123456789ABCDEF
    MASK = (1 << 64) - 1

    def new_node(x: int) -> int:
        nonlocal ptr, seed

        ptr += 1
        keys[ptr] = x

        seed = (seed + 0x9E3779B97F4A7C15) & MASK
        z = seed
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        priority[ptr] = z ^ (z >> 31)

        left[ptr] = 0
        right[ptr] = 0
        return ptr

    def merge(a: int, b: int) -> int:
        if a == 0 or b == 0:
            return a or b

        if priority[a] > priority[b]:
            right[a] = merge(right[a], b)
            return a
        else:
            left[b] = merge(a, left[b])
            return b

    def split(root: int, x: int):
        if root == 0:
            return 0, 0

        if keys[root] < x:
            a, b = split(right[root], x)
            right[root] = a
            return root, b
        else:
            a, b = split(left[root], x)
            left[root] = b
            return a, root

    def insert(root: int, x: int) -> int:
        a, b = split(root, x)
        mid, c = split(b, x + 1)

        if mid == 0:
            mid = new_node(x)

        return merge(a, merge(mid, c))

    def trim(root: int, low: int, high: int) -> int:
        a, b = split(root, low)
        mid, c = split(b, high + 1)
        return mid

    def get_min(root: int) -> int:
        if root == 0:
            return -1

        while left[root] != 0:
            root = left[root]

        return keys[root]

    karr = [0] * (n + 1)
    rep_a = [-1] * (n + 1)
    rep_b = [-1] * (n + 1)

    root_a = 0
    root_b = 0

    for i in range(1, n + 1):
        k = next(it)
        al = next(it)
        bl = next(it)
        ar = next(it)
        br = next(it)

        karr[i] = k

        if i == 1:
            if al <= k <= bl and ar <= 0 <= br:
                root_a = insert(root_a, 0)

            if ar <= k <= br and al <= 0 <= bl:
                root_b = insert(root_b, 0)

        else:
            prev_a_nonempty = root_a != 0
            prev_b_nonempty = root_b != 0
            prev_k = karr[i - 1]

            valid_left = al <= k <= bl
            valid_right = ar <= k <= br

            if not valid_left:
                root_a = 0
            else:
                root_a = trim(root_a, ar, br)

                if prev_b_nonempty and ar <= prev_k <= br:
                    root_a = insert(root_a, prev_k)

            if not valid_right:
                root_b = 0
            else:
                root_b = trim(root_b, al, bl)

                if prev_a_nonempty and al <= prev_k <= bl:
                    root_b = insert(root_b, prev_k)

        rep_a[i] = get_min(root_a)
        rep_b[i] = get_min(root_b)

    if rep_a[n] == -1 and rep_b[n] == -1:
        sys.stdout.write("No\n")
        return

    if rep_a[n] != -1:
        choice = 0
        value = rep_a[n]
    else:
        choice = 1
        value = rep_b[n]

    answer = [0] * (n + 1)

    for i in range(n, 0, -1):
        answer[i] = choice

        if i == 1:
            break

        opposite = 1 - choice
        opposite_rep = rep_b[i - 1] if opposite == 1 else rep_a[i - 1]

        if value == karr[i - 1] and opposite_rep != -1:
            choice = opposite
            value = opposite_rep

    sys.stdout.write("Yes\n")
    sys.stdout.write(" ".join(map(str, answer[1:])) + "\n")


if __name__ == "__main__":
    solve()