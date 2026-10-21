import sys


class Fenwick:
    __slots__ = ("n", "bit")

    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 2)

    def add(self, i, delta):
        bit = self.bit
        n = self.n
        while i <= n:
            bit[i] += delta
            i += i & -i

    def prefix_sum(self, i):
        bit = self.bit
        result = 0
        while i > 0:
            result += bit[i]
            i -= i & -i
        return result

    def range_sum(self, left, right):
        if right < left:
            return 0
        return self.prefix_sum(right) - self.prefix_sum(left - 1)


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    counts = [0] * n

    horizontals = []  # (id, y, x_left, x_right)
    verticals = []    # (id, x, y_bottom, y_top)

    max_x = 0
    max_y = 0

    p = 1
    for idx in range(n):
        x1, y1, x2, y2 = data[p], data[p + 1], data[p + 2], data[p + 3]
        p += 4

        max_x = max(max_x, x1, x2)
        max_y = max(max_y, y1, y2)

        if y1 == y2:
            x_left = min(x1, x2)
            x_right = max(x1, x2)
            horizontals.append((idx, y1, x_left, x_right))
        else:
            y_bottom = min(y1, y2)
            y_top = max(y1, y2)
            verticals.append((idx, x1, y_bottom, y_top))

    # Count intersections for each vertical road.
    if verticals:
        updates = []
        for _, y, x_left, x_right in horizontals:
            updates.append((x_left, y, 1))
            updates.append((x_right + 1, y, -1))

        updates.sort(key=lambda event: event[0])

        bit = Fenwick(max_y + 2)
        ui = 0
        update_count = len(updates)

        for vid, x, y_bottom, y_top in sorted(verticals, key=lambda item: item[1]):
            while ui < update_count and updates[ui][0] <= x:
                _, y, delta = updates[ui]
                bit.add(y, delta)
                ui += 1

            counts[vid] = bit.range_sum(y_bottom, y_top)

    # Count intersections for each horizontal road.
    if horizontals:
        updates = []
        for _, x, y_bottom, y_top in verticals:
            updates.append((y_bottom, x, 1))
            updates.append((y_top + 1, x, -1))

        updates.sort(key=lambda event: event[0])

        bit = Fenwick(max_x + 2)
        ui = 0
        update_count = len(updates)

        for hid, y, x_left, x_right in sorted(horizontals, key=lambda item: item[1]):
            while ui < update_count and updates[ui][0] <= y:
                _, x, delta = updates[ui]
                bit.add(x, delta)
                ui += 1

            counts[hid] = bit.range_sum(x_left, x_right)

    # Remove intersections where the point is an endpoint of both roads.
    horizontal_endpoints = {}
    for hid, y, x_left, x_right in horizontals:
        horizontal_endpoints[(x_left, y)] = hid
        horizontal_endpoints[(x_right, y)] = hid

    for vid, x, y_bottom, y_top in verticals:
        hid = horizontal_endpoints.get((x, y_bottom))
        if hid is not None:
            counts[hid] -= 1
            counts[vid] -= 1

        hid = horizontal_endpoints.get((x, y_top))
        if hid is not None:
            counts[hid] -= 1
            counts[vid] -= 1

    total_lights = 0
    for hid, _, _, _ in horizontals:
        total_lights += counts[hid]

    output = [
        str(total_lights),
        " ".join(map(str, counts))
    ]

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()