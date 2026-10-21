import sys
from array import array


def solve():
    input = sys.stdin.buffer.readline
    line = input()
    if not line:
        return

    N = int(line)

    A = array('i', [0]) * N
    B = array('i', [0]) * N

    for i in range(N):
        a, b = map(int, input().split())
        A[i] = a
        B[i] = b

    max_q = array('i', [0]) * N
    min_q = array('i', [0]) * N

    head_max = tail_max = 0
    head_min = tail_min = 0

    left = 0
    ans = 0

    for right in range(N):
        ar = A[right]
        while tail_max > head_max and A[max_q[tail_max - 1]] <= ar:
            tail_max -= 1
        max_q[tail_max] = right
        tail_max += 1

        br = B[right]
        while tail_min > head_min and B[min_q[tail_min - 1]] >= br:
            tail_min -= 1
        min_q[tail_min] = right
        tail_min += 1

        while True:
            max_a = A[max_q[head_max]]
            min_b = B[min_q[head_min]]
            width = min_b - max_a + 1
            length = right - left + 1

            if width >= length:
                break

            if max_q[head_max] == left:
                head_max += 1
            if min_q[head_min] == left:
                head_min += 1

            left += 1

        current_length = right - left + 1
        if current_length > ans:
            ans = current_length

    sys.stdout.write(str(ans) + "\n")


if __name__ == "__main__":
    solve()