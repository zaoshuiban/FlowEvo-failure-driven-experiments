import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n, a, b = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        count_a = 0
        count_b = 0

        for _ in range(n):
            x = data[idx]
            idx += 1
            if x == a:
                count_a += 1
            if x == b:
                count_b += 1

        probability = (count_a * count_b) / (n * n)
        ans.append(f"{probability:.10f}")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()