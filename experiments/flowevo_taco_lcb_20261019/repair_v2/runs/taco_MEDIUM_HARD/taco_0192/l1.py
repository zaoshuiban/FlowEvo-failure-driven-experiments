import sys

MOD = 1_000_000_007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        base = (pow(2, n, MOD) - 1) % MOD
        ans.append(str(pow(base, m, MOD)))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()