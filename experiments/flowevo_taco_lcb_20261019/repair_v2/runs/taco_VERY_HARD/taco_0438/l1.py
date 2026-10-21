import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        pref = [0] * n
        cur = 0

        for i in range(n):
            cur ^= data[idx]
            idx += 1
            pref[i] = cur

        total_xor = cur

        freq = {}
        distinct = 0

        for x in pref:
            if x in freq:
                freq[x] += 1
            else:
                freq[x] = 1
                distinct += 1

        ans = distinct

        for i in range(n - 1):
            y = total_xor ^ pref[i]

            c = freq.get(y, 0)
            if c == 0:
                distinct += 1
            freq[y] = c + 1

            x = pref[i]
            c = freq[x]

            if c == 1:
                distinct -= 1
                del freq[x]
            else:
                freq[x] = c - 1

            if distinct > ans:
                ans = distinct

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()