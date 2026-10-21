import sys


def intersection_count(c1, c2):
    x1, y1, r1 = c1
    x2, y2, r2 = c2

    dx = x1 - x2
    dy = y1 - y2
    d2 = dx * dx + dy * dy

    sum_r = r1 + r2
    diff_r = r1 - r2

    if d2 > sum_r * sum_r:
        return 0
    if d2 < diff_r * diff_r:
        return 0
    if d2 == sum_r * sum_r or d2 == diff_r * diff_r:
        return 1
    return 2


def radical_line(c1, c2):
    x1, y1, r1 = c1
    x2, y2, r2 = c2

    a = 2 * (x2 - x1)
    b = 2 * (y2 - y1)
    c = (x2 * x2 + y2 * y2 - r2 * r2) - (x1 * x1 + y1 * y1 - r1 * r1)
    return a, b, c


def common_points_count(circles, m):
    if m[0][1] == 0 or m[0][2] == 0 or m[1][2] == 0:
        return 0

    a1, b1, c1 = radical_line(circles[0], circles[1])
    a2, b2, c2 = radical_line(circles[0], circles[2])

    det = a1 * b2 - a2 * b1

    if det != 0:
        x_num = c1 * b2 - c2 * b1
        y_num = a1 * c2 - a2 * c1

        x0, y0, r0 = circles[0]
        const = x0 * x0 + y0 * y0 - r0 * r0

        value = (
            x_num * x_num
            + y_num * y_num
            - 2 * x0 * x_num * det
            - 2 * y0 * y_num * det
            + const * det * det
        )

        return 1 if value == 0 else 0

    same_line = (
        a1 * b2 == a2 * b1
        and a1 * c2 == a2 * c1
        and b1 * c2 == b2 * c1
    )

    return m[0][1] if same_line else 0


def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    circles = []
    idx = 1

    for _ in range(n):
        x = int(data[idx])
        y = int(data[idx + 1])
        r = int(data[idx + 2])
        idx += 3
        circles.append((x, y, r))

    m = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            cnt = intersection_count(circles[i], circles[j])
            m[i][j] = m[j][i] = cnt

    q = common_points_count(circles, m) if n == 3 else 0

    total_pair_intersections = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_pair_intersections += m[i][j]

    distinct_intersection_points = total_pair_intersections - 2 * q

    k = [0] * n

    if n == 1:
        k[0] = 0
    elif n == 2:
        k[0] = k[1] = m[0][1]
    else:
        k[0] = m[0][1] + m[0][2] - q
        k[1] = m[0][1] + m[1][2] - q
        k[2] = m[0][2] + m[1][2] - q

    isolated_vertices = sum(1 for x in k if x == 0)
    edges = sum(x if x > 0 else 1 for x in k)
    vertices = distinct_intersection_points + isolated_vertices

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if m[i][j] > 0:
                union(i, j)

    components = len({find(i) for i in range(n)})

    regions = edges - vertices + components + 1
    print(regions)


if __name__ == "__main__":
    solve()