import sys


def main():
    input = sys.stdin.buffer.readline

    N = int(input())
    s = bytearray(input().strip())
    Q = int(input())

    ops = []
    last_global = -1

    for i in range(Q):
        parts = input().split()
        t = int(parts[0])
        x = int(parts[1])
        c = parts[2]
        ops.append((t, x, c))
        if t != 1:
            last_global = i

    if last_global == -1:
        for t, x, c in ops:
            if t == 1:
                s[x - 1] = c[0]
    else:
        for i in range(last_global):
            t, x, c = ops[i]
            if t == 1:
                s[x - 1] = c[0]

        t, x, c = ops[last_global]
        if t == 2:
            s = s.lower()
        else:
            s = s.upper()

        for i in range(last_global + 1, Q):
            t, x, c = ops[i]
            if t == 1:
                s[x - 1] = c[0]

    sys.stdout.buffer.write(s)
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()