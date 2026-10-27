import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return
    n = data[0]
    arr = data[1:1+n]
    if not arr:
        print(0)
        return

    max_val = max(arr)
    freq = [0] * (max_val + 2)
    for x in arr:
        freq[x] += 1

    dp = [0] * (max_val + 2)
    dp[1] = freq[1] * 1

    for i in range(2, max_val + 1):
        take = dp[i-2] + freq[i] * i
        skip = dp[i-1]
        dp[i] = take if take > skip else skip

    print(dp[max_val])

if __name__ == "__main__":
    main()