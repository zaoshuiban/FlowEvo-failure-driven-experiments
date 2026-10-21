import sys

MOD = 998244353

def main():
    data = sys.stdin.buffer.read().split()
    H = int(data[0])
    W = int(data[1])
    grid = b"".join(data[2:2 + H])
    N = H * W

    labels = [-1] * N
    comp_count = 0
    HASH = ord('#')
    DOT = ord('.')

    for start in range(N):
        if grid[start] == HASH and labels[start] == -1:
            labels[start] = comp_count
            stack = [start]

            while stack:
                p = stack.pop()
                col = p % W

                q = p - W
                if q >= 0 and grid[q] == HASH and labels[q] == -1:
                    labels[q] = comp_count
                    stack.append(q)

                q = p + W
                if q < N and grid[q] == HASH and labels[q] == -1:
                    labels[q] = comp_count
                    stack.append(q)

                if col > 0:
                    q = p - 1
                    if grid[q] == HASH and labels[q] == -1:
                        labels[q] = comp_count
                        stack.append(q)

                if col + 1 < W:
                    q = p + 1
                    if grid[q] == HASH and labels[q] == -1:
                        labels[q] = comp_count
                        stack.append(q)

            comp_count += 1

    red_count = 0
    sum_adjacent_components = 0

    for p, cell in enumerate(grid):
        if cell == DOT:
            red_count += 1
            col = p % W

            up = labels[p - W] if p >= W else -1
            down = labels[p + W] if p + W < N else -1
            left = labels[p - 1] if col > 0 else -1
            right = labels[p + 1] if col + 1 < W else -1

            distinct = 0
            distinct += (up >= 0)
            distinct += (down >= 0 and down != up)
            distinct += (left >= 0 and left != up and left != down)
            distinct += (right >= 0 and right != up and right != down and right != left)

            sum_adjacent_components += distinct

    ans = (comp_count + 1) % MOD
    ans -= sum_adjacent_components * pow(red_count, MOD - 2, MOD)
    ans %= MOD

    print(ans)


if __name__ == "__main__":
    main()