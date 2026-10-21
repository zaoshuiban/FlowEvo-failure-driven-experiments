import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    t = data[1]
    lt = len(t)

    ans = []

    for idx in range(n):
        s = data[2 + idx]
        ls = len(s)
        diff_len = ls - lt

        if diff_len < -1 or diff_len > 1:
            continue

        if diff_len == 0:
            mismatch = 0
            for a, b in zip(s, t):
                if a != b:
                    mismatch += 1
                    if mismatch > 1:
                        break

            if mismatch <= 1:
                ans.append(idx + 1)

        else:
            if diff_len < 0:
                short = s
                long = t
            else:
                short = t
                long = s

            i = 0
            j = 0
            short_len = len(short)
            long_len = len(long)
            skipped = False
            ok = True

            while i < short_len and j < long_len:
                if short[i] == long[j]:
                    i += 1
                    j += 1
                else:
                    if skipped:
                        ok = False
                        break
                    skipped = True
                    j += 1

            if ok and i == short_len:
                ans.append(idx + 1)

    output = [str(len(ans))]
    if ans:
        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()