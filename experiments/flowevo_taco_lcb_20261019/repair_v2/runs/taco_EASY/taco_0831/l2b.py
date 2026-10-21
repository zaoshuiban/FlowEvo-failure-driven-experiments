import sys

def main():
    n = int(sys.stdin.readline())
    total = n * (n + 1) // 2
    target = total // 2

    chosen = []
    remaining = target

    for x in range(n, 0, -1):
        if x <= remaining:
            chosen.append(x)
            remaining -= x
            if remaining == 0:
                break

    print(total % 2)
    print(len(chosen), *chosen)

if __name__ == "__main__":
    main()