import sys

MOD = 1_000_000_007

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    T = data[idx]
    idx += 1

    outputs = []

    for _ in range(T):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        commands = [None] * (m + 1)

        for i in range(1, m + 1):
            t = data[idx]
            l = data[idx + 1]
            r = data[idx + 2]
            idx += 3
            commands[i] = (t, l, r)

        count = [0] * (m + 2)
        events = [0] * (m + 2)

        active = 0

        for i in range(m, 0, -1):
            active = (active + events[i]) % MOD
            count[i] = (active + 1) % MOD

            t, l, r = commands[i]
            if t == 2:
                val = count[i]
                events[r] = (events[r] + val) % MOD
                events[l - 1] = (events[l - 1] - val) % MOD

        diff = [0] * (n + 3)

        for i in range(1, m + 1):
            t, l, r = commands[i]
            if t == 1:
                val = count[i]
                diff[l] = (diff[l] + val) % MOD
                diff[r + 1] = (diff[r + 1] - val) % MOD

        ans = []
        cur = 0

        for i in range(1, n + 1):
            cur = (cur + diff[i]) % MOD
            ans.append(str(cur))

        outputs.append(" ".join(ans))

    sys.stdout.write("\n".join(outputs))


if __name__ == "__main__":
    solve()