import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    MOD = 10**8
    a.sort()

    ans = (n - 1) * sum(a)

    less = 0
    j = n - 1
    for i in range(n):
        while j > i and a[i] + a[j] >= MOD:
            j -= 1
        if j > i:
            less += j - i

    total_pairs = n * (n - 1) // 2
    count_ge = total_pairs - less

    ans -= MOD * count_ge
    print(ans)

if __name__ == "__main__":
    main()