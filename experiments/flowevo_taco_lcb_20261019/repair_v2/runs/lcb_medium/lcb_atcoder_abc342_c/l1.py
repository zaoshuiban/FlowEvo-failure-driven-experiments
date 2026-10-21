import sys

def main():
    data = sys.stdin.buffer.read().split()

    N = int(data[0])
    S = data[1]
    Q = int(data[2])

    mp = list(range(26))

    idx = 3
    for _ in range(Q):
        c = data[idx][0] - ord('a')
        d = data[idx + 1][0] - ord('a')
        idx += 2

        for i in range(26):
            if mp[i] == c:
                mp[i] = d

    ans = bytes(mp[ch - ord('a')] + ord('a') for ch in S)
    sys.stdout.buffer.write(ans + b'\n')

if __name__ == "__main__":
    main()