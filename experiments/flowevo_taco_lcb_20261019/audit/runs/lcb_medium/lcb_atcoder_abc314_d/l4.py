import sys


def main():
    data = sys.stdin.buffer.read().split()

    N = int(data[0])
    S = bytearray(data[1])
    Q = int(data[2])

    # Find the last operation of type 2 or 3.
    last_global = 0
    base = 3
    for i in range(1, Q + 1):
        t = data[base + (i - 1) * 3]
        if t != b'1':
            last_global = i

    # Apply type-1 operations up to the last global case conversion.
    idx = 3
    for i in range(1, last_global + 1):
        t = data[idx]
        if t == b'1':
            x = int(data[idx + 1]) - 1
            S[x] = data[idx + 2][0]
        idx += 3

    # Apply the final global case conversion.
    if last_global > 0:
        global_type = int(data[3 + (last_global - 1) * 3])

        if global_type == 2:
            for i in range(N):
                ch = S[i]
                if 65 <= ch <= 90:
                    S[i] = ch + 32
        else:
            for i in range(N):
                ch = S[i]
                if 97 <= ch <= 122:
                    S[i] = ch - 32

    # Apply type-1 operations after the last global case conversion.
    idx = 3 + last_global * 3
    for _ in range(last_global + 1, Q + 1):
        t = data[idx]
        if t == b'1':
            x = int(data[idx + 1]) - 1
            S[x] = data[idx + 2][0]
        idx += 3

    sys.stdout.buffer.write(bytes(S) + b'\n')


if __name__ == "__main__":
    main()