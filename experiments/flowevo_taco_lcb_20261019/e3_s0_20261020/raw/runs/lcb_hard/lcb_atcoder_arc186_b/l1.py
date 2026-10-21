import sys

MOD = 998244353

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N = data[0]
    A = [0] + data[1:1 + N]

    parent = [0] * (N + 1)
    stack = []

    for i in range(1, N + 1):
        a = A[i]
        last = 0

        if a == 0:
            while stack:
                last = stack.pop()
        else:
            while stack and stack[-1] != a:
                last = stack.pop()

        parent[i] = a
        if last:
            parent[last] = i

        stack.append(i)

    children = [[] for _ in range(N + 1)]
    roots = []

    for v in range(1, N + 1):
        p = parent[v]
        if p == 0:
            roots.append(v)
        else:
            children[p].append(v)

    order = []
    st = roots[:]

    while st:
        v = st.pop()
        order.append(v)
        for c in children[v]:
            st.append(c)

    size = [1] * (N + 1)
    prod_size = 1

    for v in reversed(order):
        s = size[v]
        prod_size = prod_size * s % MOD
        p = parent[v]
        if p:
            size[p] += s

    fact = 1
    for i in range(2, N + 1):
        fact = fact * i % MOD

    answer = fact * pow(prod_size, MOD - 2, MOD) % MOD
    print(answer)


if __name__ == "__main__":
    main()