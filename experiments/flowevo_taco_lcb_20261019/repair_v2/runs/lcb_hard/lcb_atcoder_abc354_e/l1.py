import sys

def main():
    input = sys.stdin.readline

    N = int(input())
    A = [0] * N
    B = [0] * N
    for i in range(N):
        A[i], B[i] = map(int, input().split())

    adj = [0] * N
    for i in range(N):
        mask = 0
        for j in range(N):
            if i != j and (A[i] == A[j] or B[i] == B[j]):
                mask |= 1 << j
        adj[i] = mask

    total = 1 << N
    win = bytearray(total)

    for mask in range(total):
        m = mask
        can_win = 0

        while m:
            lsb = m & -m
            i = lsb.bit_length() - 1
            m ^= lsb

            candidates = m & adj[i]
            while candidates:
                other = candidates & -candidates
                nxt = mask ^ lsb ^ other

                if win[nxt] == 0:
                    can_win = 1
                    break

                candidates ^= other

            if can_win:
                break

        win[mask] = can_win

    print("Takahashi" if win[total - 1] else "Aoki")


if __name__ == "__main__":
    main()