import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    T = int(data[0])
    answers = []

    for case in range(1, T + 1):
        t = data[case]
        n = len(t)

        freq = [0] * 26
        for ch in t:
            freq[ch - 97] += 1

        seen = [False] * 26
        reversed_order = []

        for ch in reversed(t):
            idx = ch - 97
            if not seen[idx]:
                seen[idx] = True
                reversed_order.append(idx)

        order = reversed_order[::-1]
        rem_pos = [0] * 26

        ok = True
        initial_len = 0

        for pos, idx in enumerate(order, 1):
            rem_pos[idx] = pos
            if freq[idx] % pos != 0:
                ok = False
                break
            initial_len += freq[idx] // pos

        if not ok or initial_len > n:
            answers.append(b"-1")
            continue

        s = t[:initial_len]

        s_freq = [0] * 26
        for ch in s:
            s_freq[ch - 97] += 1

        for idx in order:
            if s_freq[idx] != freq[idx] // rem_pos[idx]:
                ok = False
                break

        if not ok:
            answers.append(b"-1")
            continue

        k = len(order)
        pos_t = 0

        for stage in range(k):
            for ch in s:
                idx = ch - 97
                if rem_pos[idx] > stage:
                    if pos_t >= n or t[pos_t] != ch:
                        ok = False
                        break
                    pos_t += 1
            if not ok:
                break

        if ok and pos_t == n:
            order_bytes = bytes(x + 97 for x in order)
            answers.append(s + b" " + order_bytes)
        else:
            answers.append(b"-1")

    sys.stdout.buffer.write(b"\n".join(answers))


if __name__ == "__main__":
    main()