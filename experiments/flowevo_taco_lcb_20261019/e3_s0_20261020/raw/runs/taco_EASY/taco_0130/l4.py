import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a1 = data[idx]
        idx += 1

        mn = 10**18
        for _ in range(n - 1):
            v = data[idx]
            idx += 1
            if v < mn:
                mn = v

        if a1 > mn:
            ans.append("Alice")
        else:
            ans.append("Bob")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()