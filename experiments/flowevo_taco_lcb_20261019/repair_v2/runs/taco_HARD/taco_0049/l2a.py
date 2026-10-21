import sys
from array import array


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    m = data[1]

    u = array('i')
    v = array('i')
    w = array('i')

    p = 2
    for _ in range(m):
        u.append(data[p] - 1)
        v.append(data[p + 1] - 1)
        w.append(data[p + 2])
        p += 3

    del data

    if n == 1:
        return

    order = list(range(m))
    order.sort(key=w.__getitem__)

    parent = list(range(n))
    size = [1] * n

    head = array('i', [-1]) * n
    to = array('i')
    weight = array('i')
    nxt = array('i')

    is_tree = bytearray(m)
    total = 0
    used = 0
    need = n - 1

    for idx in order:
        a = u[idx]
        b = v[idx]

        x = a
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        ra = x

        x = b
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        rb = x

        if ra == rb:
            continue

        if size[ra] < size[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        size[ra] += size[rb]

        c = w[idx]
        total += c
        is_tree[idx] = 1

        pos = len(to)
        to.append(b)
        weight.append(c)
        nxt.append(head[a])
        head[a] = pos

        pos = len(to)
        to.append(a)
        weight.append(c)
        nxt.append(head[b])
        head[b] = pos

        used += 1
        if used == need:
            break

    LOG = max(1, n.bit_length())

    up0 = array('i', [-1]) * n
    mx0 = array('i', [0]) * n
    depth = array('i', [0]) * n

    up0[0] = 0
    stack = [0]

    while stack:
        x = stack.pop()
        e = head[x]
        nd = depth[x] + 1

        while e != -1:
            y = to[e]
            if up0[y] == -1:
                up0[y] = x
                mx0[y] = weight[e]
                depth[y] = nd
                stack.append(y)
            e = nxt[e]

    up = [up0]
    mx = [mx0]

    for _ in range(1, LOG):
        prev_up = up[-1]
        prev_mx = mx[-1]

        cur_up = array('i', [0]) * n
        cur_mx = array('i', [0]) * n

        for i in range(n):
            par = prev_up[i]
            cur_up[i] = prev_up[par]

            best = prev_mx[i]
            other = prev_mx[par]
            if other > best:
                best = other
            cur_mx[i] = best

        up.append(cur_up)
        mx.append(cur_mx)

    def max_on_path(a, b):
        answer = 0

        if depth[a] < depth[b]:
            a, b = b, a

        diff = depth[a] - depth[b]
        bit = 0

        while diff:
            if diff & 1:
                val = mx[bit][a]
                if val > answer:
                    answer = val
                a = up[bit][a]

            diff >>= 1
            bit += 1

        if a == b:
            return answer

        for k in range(LOG - 1, -1, -1):
            ua = up[k][a]
            ub = up[k][b]

            if ua != ub:
                val = mx[k][a]
                if val > answer:
                    answer = val

                val = mx[k][b]
                if val > answer:
                    answer = val

                a = ua
                b = ub

        val = mx[0][a]
        if val > answer:
            answer = val

        val = mx[0][b]
        if val > answer:
            answer = val

        return answer

    result = []
    append = result.append

    for i in range(m):
        if is_tree[i]:
            append(str(total))
        else:
            maximum = max_on_path(u[i], v[i])
            append(str(total + w[i] - maximum))

    sys.stdout.write("\n".join(result))


if __name__ == "__main__":
    main()