import sys
from array import array


def solve():
    input = sys.stdin.buffer.readline
    line = input()
    if not line:
        return

    N = int(line)

    max_idx = array('i', [0]) * N
    max_val = array('i', [0]) * N
    min_idx = array('i', [0]) * N
    min_val = array('i', [0]) * N

    head_max = tail_max = 0
    head_min = tail_min = 0

    left = 0
    ans = 0

    for right in range(N):
        a, b = map(int, input().split())

        while tail_max > head_max and max_val[tail_max - 1] <= a:
            tail_max -= 1
        max_idx[tail_max] = right
        max_val[tail_max] = a
        tail_max += 1

        while tail_min > head_min and min_val[tail_min - 1] >= b:
            tail_min -= 1
        min_idx[tail_min] = right
        min_val[tail_min] = b
        tail_min += 1

        while True:
            max_a = max_val[head_max]
            min_b = min_val[head_min]
            length = right - left + 1

            if min_b - max_a + 1 >= length:
                break

            if max_idx[head_max] == left:
                head_max += 1
            if min_idx[head_min] == left:
                head_min += 1
            left += 1

        length = right - left + 1
        if length > ans:
            ans = length

    sys.stdout.write(str(ans) + "\n")


if __name__ == "__main__":
    solve()