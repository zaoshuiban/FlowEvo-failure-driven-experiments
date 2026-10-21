import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    ans = []
    idx = 1
    for _ in range(n):
        k = int(data[idx])
        x = int(data[idx + 1])
        idx += 2
        ans.append(str(x + (k - 1) * 9))
    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()