import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)

    min_r1 = 10**18
    max_l1 = -1

    for _ in range(n):
        l = next(it)
        r = next(it)
        min_r1 = min(min_r1, r)
        max_l1 = max(max_l1, l)

    m = next(it)

    min_r2 = 10**18
    max_l2 = -1

    for _ in range(m):
        l = next(it)
        r = next(it)
        min_r2 = min(min_r2, r)
        max_l2 = max(max_l2, l)

    answer = max(0, max_l2 - min_r1, max_l1 - min_r2)
    print(answer)

if __name__ == "__main__":
    main()