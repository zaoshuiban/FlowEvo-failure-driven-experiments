import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    output = []

    for _ in range(t):
        n = int(data[idx])
        idx += 1

        if n == 1:
            output.append("0")
            continue

        outgoing = {}
        incoming = set()
        total_cost = 0

        for _ in range(n - 1):
            a = data[idx].decode()
            b = data[idx + 1].decode()
            c = int(data[idx + 2])
            idx += 3

            outgoing[a] = (b, c)
            incoming.add(b)
            total_cost += c

        start = None
        for city in outgoing:
            if city not in incoming:
                start = city
                break

        current = start
        for _ in range(n - 1):
            nxt, cost = outgoing[current]
            output.append(f"{current} {nxt} {cost}")
            current = nxt

        output.append(str(total_cost))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()