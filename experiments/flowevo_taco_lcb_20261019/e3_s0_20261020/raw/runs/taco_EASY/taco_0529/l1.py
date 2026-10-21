import sys

def main():
    input = sys.stdin.readline
    n = int(input())
    counts = [0] * 26

    for _ in range(n):
        name = input().strip()
        counts[ord(name[0]) - ord('a')] += 1

    answer = 0

    for k in counts:
        best = float('inf')
        for left in range(k + 1):
            right = k - left
            pairs = left * (left - 1) // 2 + right * (right - 1) // 2
            best = min(best, pairs)
        answer += best

    print(answer)

if __name__ == "__main__":
    main()