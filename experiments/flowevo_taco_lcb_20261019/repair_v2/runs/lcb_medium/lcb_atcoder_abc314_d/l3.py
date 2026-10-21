import sys


def main():
    input = sys.stdin.buffer.readline

    n_line = input()
    if not n_line:
        return

    N = int(n_line)
    S = bytearray(input().strip())
    Q = int(input())

    last_update = [0] * N
    last_type = 0
    last_time = 0

    for i in range(1, Q + 1):
        parts = input().split()
        t = int(parts[0])

        if t == 1:
            x = int(parts[1]) - 1
            c = parts[2][0]
            S[x] = c
            last_update[x] = i
        else:
            last_type = t
            last_time = i

    if last_time != 0:
        if last_type == 2:
            for i in range(N):
                if last_update[i] < last_time:
                    ch = S[i]
                    if 65 <= ch <= 90:
                        S[i] = ch + 32
        else:
            for i in range(N):
                if last_update[i] < last_time:
                    ch = S[i]
                    if 97 <= ch <= 122:
                        S[i] = ch - 32

    sys.stdout.buffer.write(S)
    sys.stdout.buffer.write(b'\n')


if __name__ == "__main__":
    main()