import sys

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, M = data[0], data[1]

    INF = M + 1
    min_r_at_l = [INF] * (M + 2)

    idx = 2
    for _ in range(N):
        l = data[idx]
        r = data[idx + 1]
        idx += 2
        if r < min_r_at_l[l]:
            min_r_at_l[l] = r

    ans = 0
    current_min_r = INF

    for l in range(M, 0, -1):
        if min_r_at_l[l] < current_min_r:
            current_min_r = min_r_at_l[l]
        ans += current_min_r - l

    print(ans)

if __name__ == "__main__":
    main()