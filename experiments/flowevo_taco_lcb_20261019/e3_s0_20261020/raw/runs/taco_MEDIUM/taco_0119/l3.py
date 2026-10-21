import sys

def main():
    n, m = map(int, sys.stdin.readline().split())
    k = min(n, m)

    ans = [str(k + 1)]
    for i in range(k + 1):
        ans.append(f"{i} {k - i}")

    sys.stdout.write("\n".join(ans) + "\n")

if __name__ == "__main__":
    main()