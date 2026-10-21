import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        x = data[idx:idx + n]
        idx += n

        nim_sum = 0
        for ai, xi in zip(a, x):
            nim_sum ^= (xi - 1)
            nim_sum ^= (ai - xi)

        ans.append("First" if nim_sum != 0 else "Second")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()