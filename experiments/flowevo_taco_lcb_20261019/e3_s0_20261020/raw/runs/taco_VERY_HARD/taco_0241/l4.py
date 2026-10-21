import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    out = []

    for _ in range(t):
        n = data[idx]
        idx += 1
        c = data[idx]
        idx += 1

        left_count = 0
        right_count = 0
        max_left = None
        min_right = None

        for _ in range(n):
            p = data[idx]
            idx += 1

            if p < c:
                left_count += 1
                if max_left is None or p > max_left:
                    max_left = p
            else:  # p > c is guaranteed
                right_count += 1
                if min_right is None or p < min_right:
                    min_right = p

        left_odd = left_count > 0 and ((c - max_left) & 1) == 1
        right_odd = right_count > 0 and ((min_right - c) & 1) == 1

        eliminated = 0
        if left_odd:
            eliminated += left_count
        if right_odd:
            eliminated += right_count

        all_sides_odd = (left_count == 0 or left_odd) and (right_count == 0 or right_odd)
        escaped = 1 if all_sides_odd else -1

        out.append(f"{eliminated} {escaped}")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()