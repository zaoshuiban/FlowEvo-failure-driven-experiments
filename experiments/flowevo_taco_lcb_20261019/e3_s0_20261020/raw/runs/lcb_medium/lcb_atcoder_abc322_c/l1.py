import sys

def main():
    input = sys.stdin.readline
    N, M = map(int, input().split())
    A = list(map(int, input().split()))

    ans = [0] * (N + 1)
    j = M - 1
    next_firework = N

    for day in range(N, 0, -1):
        if j >= 0 and A[j] == day:
            next_firework = day
            j -= 1
        ans[day] = next_firework - day

    print('\n'.join(map(str, ans[1:])))

if __name__ == "__main__":
    main()