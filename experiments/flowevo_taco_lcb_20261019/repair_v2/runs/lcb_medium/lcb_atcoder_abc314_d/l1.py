import sys


def main():
    input = sys.stdin.buffer.readline

    N = int(input())
    S = input().strip()
    Q = int(input())

    ops = []
    last_case_op = -1
    last_case_type = 0

    for i in range(Q):
        t, x, c = input().split()
        t = int(t)
        x = int(x)

        if t == 1:
            ops.append((1, x - 1, c[0]))
        else:
            ops.append((t, 0, 0))
            last_case_op = i
            last_case_type = t

    arr = bytearray(S)

    for i, (t, x, c) in enumerate(ops):
        if i == last_case_op:
            if last_case_type == 2:
                arr = bytearray(arr.lower())
            elif last_case_type == 3:
                arr = bytearray(arr.upper())

        if t == 1:
            arr[x] = c

    sys.stdout.buffer.write(arr)
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()