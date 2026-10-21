import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, x1, x2 = data[0], data[1], data[2]
    c = data[3:3 + n]

    servers = [(c[i], i + 1) for i in range(n)]
    servers.sort(reverse=True)

    a = [server[0] for server in servers]
    original_index = [server[1] for server in servers]

    def try_order(x_first, x_second):
        max_value = [-10**18] * (n + 1)
        arg_max = [-1] * (n + 1)

        for t in range(n - 1, -1, -1):
            need = (x_second + a[t] - 1) // a[t]
            value = (t + 1) - need

            if value >= max_value[t + 1]:
                max_value[t] = value
                arg_max[t] = t
            else:
                max_value[t] = max_value[t + 1]
                arg_max[t] = arg_max[t + 1]

        for p in range(1, n):
            if a[p - 1] * p >= x_first and max_value[p] >= p:
                t = arg_max[p]
                return p, t

        return None

    result = try_order(x1, x2)

    if result is not None:
        p, t = result
        k1 = p
        k2 = t - p + 1

        first_service = [str(original_index[i]) for i in range(0, p)]
        second_service = [str(original_index[i]) for i in range(p, t + 1)]

        output = [
            "Yes",
            f"{k1} {k2}",
            " ".join(first_service),
            " ".join(second_service)
        ]
        sys.stdout.write("\n".join(output))
        return

    result = try_order(x2, x1)

    if result is not None:
        p, t = result
        k2 = p
        k1 = t - p + 1

        first_service = [str(original_index[i]) for i in range(p, t + 1)]
        second_service = [str(original_index[i]) for i in range(0, p)]

        output = [
            "Yes",
            f"{k1} {k2}",
            " ".join(first_service),
            " ".join(second_service)
        ]
        sys.stdout.write("\n".join(output))
        return

    sys.stdout.write("No")


if __name__ == "__main__":
    main()