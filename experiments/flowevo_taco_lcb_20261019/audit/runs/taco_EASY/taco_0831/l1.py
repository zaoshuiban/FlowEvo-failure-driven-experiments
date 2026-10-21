import sys

def main():
    n = int(sys.stdin.readline())
    total = n * (n + 1) // 2
    target = total // 2

    remaining = target
    group = []

    for x in range(n, 0, -1):
        if x <= remaining:
            group.append(x)
            remaining -= x
            if remaining == 0:
                break

    difference = total - 2 * target

    print(difference)
    print(len(group), *group)

if __name__ == "__main__":
    main()