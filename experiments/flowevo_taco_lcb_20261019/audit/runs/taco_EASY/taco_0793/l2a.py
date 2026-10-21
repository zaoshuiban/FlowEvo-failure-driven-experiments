import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    m = data[0]
    A = data[1:1 + m]
    B = data[1 + m:1 + 2 * m]

    A.sort(reverse=True)
    order = sorted(range(m), key=B.__getitem__)  # increasing B

    ans = [0] * m
    for a, idx in zip(A, order):
        ans[idx] = a

    sys.stdout.write(' '.join(map(str, ans)))

if __name__ == "__main__":
    main()