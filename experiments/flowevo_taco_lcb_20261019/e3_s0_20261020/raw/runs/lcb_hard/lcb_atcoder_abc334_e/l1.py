import sys

MOD = 998244353


def main():
    input = sys.stdin.buffer.readline
    H, W = map(int, input().split())

    stride = W + 2
    size = (H + 2) * stride
    grid = bytearray(size)
    red_count = 0

    for i in range(1, H + 1):
        line = input().strip()
        start = i * stride + 1
        grid[start:start + W] = line
        red_count += line.count(b'.')

    visited = bytearray(size)
    seen_red = [0] * size

    components = 0
    sum_adjacent_red = 0

    g = grid
    vis = visited
    seen = seen_red
    stp = stride

    for start in range(size):
        if g[start] != ord('#') or vis[start]:
            continue

        components += 1
        vis[start] = 1
        stack = [start]
        adjacent_red_count = 0

        while stack:
            v = stack.pop()

            u = v + 1
            val = g[u]
            if val == ord('#'):
                if not vis[u]:
                    vis[u] = 1
                    stack.append(u)
            elif val == ord('.'):
                if seen[u] != components:
                    seen[u] = components
                    adjacent_red_count += 1

            u = v - 1
            val = g[u]
            if val == ord('#'):
                if not vis[u]:
                    vis[u] = 1
                    stack.append(u)
            elif val == ord('.'):
                if seen[u] != components:
                    seen[u] = components
                    adjacent_red_count += 1

            u = v + stp
            val = g[u]
            if val == ord('#'):
                if not vis[u]:
                    vis[u] = 1
                    stack.append(u)
            elif val == ord('.'):
                if seen[u] != components:
                    seen[u] = components
                    adjacent_red_count += 1

            u = v - stp
            val = g[u]
            if val == ord('#'):
                if not vis[u]:
                    vis[u] = 1
                    stack.append(u)
            elif val == ord('.'):
                if seen[u] != components:
                    seen[u] = components
                    adjacent_red_count += 1

        sum_adjacent_red += adjacent_red_count

    numerator = (components * red_count + red_count - sum_adjacent_red) % MOD
    answer = numerator * pow(red_count, MOD - 2, MOD) % MOD
    print(answer)


if __name__ == "__main__":
    main()