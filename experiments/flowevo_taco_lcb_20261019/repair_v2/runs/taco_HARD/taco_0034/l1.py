import sys
from array import array


def main():
    input = sys.stdin.buffer.readline

    n = int(input())

    max_val = array('i', [0]) * n
    max_idx = array('i', [0]) * n
    min_val = array('i', [0]) * n
    min_idx = array('i', [0]) * n

    head_max = tail_max = 0
    head_min = tail_min = 0

    left = 0
    answer = 0

    for right in range(n):
        a, b = map(int, input().split())

        while head_max < tail_max and max_val[tail_max - 1] <= a:
            tail_max -= 1
        max_val[tail_max] = a
        max_idx[tail_max] = right
        tail_max += 1

        while head_min < tail_min and min_val[tail_min - 1] >= b:
            tail_min -= 1
        min_val[tail_min] = b
        min_idx[tail_min] = right
        tail_min += 1

        while min_val[head_min] - max_val[head_max] + 1 < right - left + 1:
            if max_idx[head_max] == left:
                head_max += 1
            if min_idx[head_min] == left:
                head_min += 1
            left += 1

        current_length = right - left + 1
        if current_length > answer:
            answer = current_length

    print(answer)


if __name__ == "__main__":
    main()