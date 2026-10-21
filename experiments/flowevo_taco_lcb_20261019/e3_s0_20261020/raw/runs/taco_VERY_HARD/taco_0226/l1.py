import sys
import math


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    children = [[] for _ in range(n + 1)]

    idx = 1
    for node in range(2, n + 1):
        p = data[idx]
        idx += 1
        children[p].append(node)

    # Preorder list; reversed gives descendants before ancestors.
    order = []
    stack = [1]
    while stack:
        u = stack.pop()
        order.append(u)
        for v in children[u]:
            stack.append(v)

    # down[u] = first node on the unary chain starting at u that is not unary:
    # either a leaf (0 children) or a branching node (>= 2 children).
    down = [0] * (n + 1)
    for u in reversed(order):
        k = len(children[u])
        if k == 1:
            down[u] = down[children[u][0]]
        else:
            down[u] = u

    q = data[idx]
    idx += 1

    groups = [[] for _ in range(n + 1)]
    answers = [0] * q
    max_w = 0

    for qi in range(q):
        v = data[idx]
        w = data[idx + 1]
        idx += 2

        if w > max_w:
            max_w = w

        imp = down[v]
        groups[imp].append((w, qi))

    if max_w < 1:
        max_w = 1

    # Primes up to sqrt(max_w), enough for factorizing all query W.
    limit = math.isqrt(max_w) + 1
    sieve = [True] * (limit + 1)
    if limit >= 0:
        sieve[0] = False
    if limit >= 1:
        sieve[1] = False

    primes = []
    for i in range(2, limit + 1):
        if sieve[i]:
            primes.append(i)
            start = i * i
            if start <= limit:
                for j in range(start, limit + 1, i):
                    sieve[j] = False

    def divisors_of(w):
        temp = w
        divs = [1]

        for p in primes:
            if p * p > temp:
                break
            if temp % p == 0:
                old_len = len(divs)
                mult = 1
                while temp % p == 0:
                    temp //= p
                    mult *= p
                    for i in range(old_len):
                        divs.append(divs[i] * mult)

        if temp > 1:
            old_len = len(divs)
            p = temp
            for i in range(old_len):
                divs.append(divs[i] * p)

        return divs

    # F[u][d] = number of leaves in subtree of important node u such that
    # the product of child counts from u down to that leaf equals d.
    F = [None] * (n + 1)

    for u in reversed(order):
        k = len(children[u])

        if k >= 2:
            if k > max_w:
                # For every query W <= max_w < k, this node cannot divide W.
                for c in children[u]:
                    imp = down[c]
                    if len(children[imp]) >= 2:
                        F[imp] = None

                F[u] = {}

                if groups[u]:
                    for w, qi in groups[u]:
                        answers[qi] = w
                continue

            mp = {}

            for c in children[u]:
                imp = down[c]
                k_imp = len(children[imp])

                if k_imp == 0:
                    nd = k
                    if nd <= max_w:
                        mp[nd] = mp.get(nd, 0) + 1
                else:
                    child_map = F[imp]

                    if child_map:
                        for d, cnt in child_map.items():
                            nd = d * k
                            if nd <= max_w:
                                mp[nd] = mp.get(nd, 0) + cnt

                    F[imp] = None

            F[u] = mp

            if groups[u]:
                for w, qi in groups[u]:
                    executed = 0

                    for d in divisors_of(w):
                        cnt = mp.get(d, 0)
                        if cnt:
                            executed += cnt * (w // d)

                    answers[qi] = w - executed

    sys.stdout.write("\n".join(map(str, answers)))


if __name__ == "__main__":
    solve()