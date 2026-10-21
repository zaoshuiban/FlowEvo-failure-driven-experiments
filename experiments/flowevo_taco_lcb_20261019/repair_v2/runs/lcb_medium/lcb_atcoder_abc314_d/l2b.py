import sys


def main():
    data = sys.stdin.buffer.read().split()

    N = int(data[0])
    S = bytearray(data[1])
    Q = int(data[2])

    idx = 3
    upd_char = bytearray(S)
    upd_time = [0] * N

    last_type = 0
    last_time = 0

    for i in range(1, Q + 1):
        t = int(data[idx])
        x = int(data[idx + 1])
        c = data[idx + 2][0]
        idx += 3

        if t == 1:
            pos = x - 1
            upd_char[pos] = c
            upd_time[pos] = i
        else:
            last_type = t
            last_time = i

    ans = bytearray(N)

    for i in range(N):
        ch = upd_char[i]

        if upd_time[i] < last_time:
            if last_type == 2:
                if 65 <= ch <= 90:
                    ch += 32
            else:
                if 97 <= ch <= 122:
                    ch -= 32

        ans[i] = ch

    ans.append(10)
    sys.stdout.buffer.write(ans)


if __name__ == "__main__":
    main()