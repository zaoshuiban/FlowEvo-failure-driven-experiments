import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
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

    chosen_sum = target - remaining
    diff = abs(total - 2 * chosen_sum)

    chosen.reverse()

    sys.stdout.write(str(diff) + "\n")
    sys.stdout.write(str(len(chosen)) + " " + " ".join(map(str, chosen)) + "\n")


if __name__ == "__main__":
    main()