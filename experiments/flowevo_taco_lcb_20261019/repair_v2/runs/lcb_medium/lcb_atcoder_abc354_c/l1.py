import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    cards = []
    pos = 1

    for i in range(1, n + 1):
        a = int(data[pos])
        c = int(data[pos + 1])
        pos += 2
        cards.append((a, c, i))

    # Process cards from strongest to weakest.
    cards.sort(key=lambda x: -x[0])

    ans = []
    min_cost = 10**30

    for a, c, i in cards:
        if c < min_cost:
            ans.append(i)
            min_cost = c

    ans.sort()

    print(len(ans))
    print(*ans)


if __name__ == "__main__":
    main()