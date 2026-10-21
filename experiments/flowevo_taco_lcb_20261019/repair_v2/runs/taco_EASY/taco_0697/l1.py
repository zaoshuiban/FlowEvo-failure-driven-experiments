import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        a = data[idx]
        b = data[idx + 1]
        idx += 2
        ans.append(str(a + b))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()