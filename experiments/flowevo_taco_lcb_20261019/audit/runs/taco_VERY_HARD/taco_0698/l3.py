import sys

MOD = 1000000007


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    k = int(data[1])
    s = data[2]

    if k == 1:
        total = pow(2, s.count(b'X'), MOD)

        first_b = s.find(b'B')
        if first_b == -1:
            first_b = n

        last_w = s.rfind(b'W')

        # Non-beautiful strings for k = 1 are exactly strings of the form W*B*.
        non_beautiful = first_b - last_w
        if non_beautiful < 0:
            non_beautiful = 0

        ans = (total - non_beautiful) % MOD
        print(ans)
        return

    # D[r]: no B^k has appeared yet, current suffix has r consecutive B's.
    # E[r]: B^k has appeared, no W^k after it yet, current suffix has r consecutive W's.
    d = [0] * k
    e = [0] * k

    d[0] = 1

    off_d = 0
    len_d = 1
    sum_d = 1

    off_e = 0
    len_e = 0
    sum_e = 0

    mod = MOD
    kk = k

    for ch in s:
        if ch == 88:  # 'X'
            new_off_d = off_d - 1
            if new_off_d < 0:
                new_off_d += kk

            if len_d == kk:
                tail_d = d[new_off_d]
            else:
                tail_d = 0

            cross = tail_d
            spawn_d = sum_d
            sum_d = (sum_d + sum_d - tail_d) % mod

            off_d = new_off_d
            d[off_d] = spawn_d
            if len_d < kk:
                len_d += 1

            new_off_e = off_e - 1
            if new_off_e < 0:
                new_off_e += kk

            if len_e == kk:
                tail_e = e[new_off_e]
            else:
                tail_e = 0

            spawn_e = sum_e + cross
            if spawn_e >= mod:
                spawn_e -= mod

            sum_e = (sum_e + sum_e - tail_e + cross) % mod

            off_e = new_off_e
            e[off_e] = spawn_e
            if len_e < kk:
                len_e += 1

        elif ch == 66:  # 'B'
            new_off_d = off_d - 1
            if new_off_d < 0:
                new_off_d += kk

            if len_d == kk:
                tail_d = d[new_off_d]
            else:
                tail_d = 0

            cross = tail_d
            sum_d -= tail_d
            if sum_d < 0:
                sum_d += mod

            off_d = new_off_d
            d[off_d] = 0
            if len_d < kk:
                len_d += 1

            val = sum_e + cross
            if val >= mod:
                val -= mod

            e[off_e] = val
            sum_e = val
            len_e = 1

        else:  # 'W'
            d[off_d] = sum_d
            len_d = 1

            new_off_e = off_e - 1
            if new_off_e < 0:
                new_off_e += kk

            if len_e == kk:
                tail_e = e[new_off_e]
            else:
                tail_e = 0

            sum_e -= tail_e
            if sum_e < 0:
                sum_e += mod

            off_e = new_off_e
            e[off_e] = 0

            if len_e != 0 and len_e < kk:
                len_e += 1

    non_beautiful = sum_d + sum_e
    if non_beautiful >= mod:
        non_beautiful -= mod

    total = pow(2, s.count(b'X'), mod)
    answer = (total - non_beautiful) % mod
    print(answer)


if __name__ == "__main__":
    main()