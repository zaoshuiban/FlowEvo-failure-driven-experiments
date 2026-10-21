import sys

def main():
    data_in = sys.stdin.buffer
    first = data_in.readline()
    if not first:
        return

    n = int(first)
    q = (n - 1).bit_length()

    responses = []

    for t in range(q):
        # Query indices whose t-th bit is 1.
        ones = [str(i + 1) for i in range(n) if ((i >> t) & 1)]
        sys.stdout.write(str(len(ones)) + "\n")
        sys.stdout.write(" ".join(ones) + "\n")
        sys.stdout.flush()

        arr = list(map(int, data_in.readline().split()))
        while len(arr) < n:
            arr.extend(map(int, data_in.readline().split()))
        responses.append((t, 1, arr))

        # Query indices whose t-th bit is 0.
        zeros = [str(i + 1) for i in range(n) if (((i >> t) & 1) == 0)]
        sys.stdout.write(str(len(zeros)) + "\n")
        sys.stdout.write(" ".join(zeros) + "\n")
        sys.stdout.flush()

        arr = list(map(int, data_in.readline().split()))
        while len(arr) < n:
            arr.extend(map(int, data_in.readline().split()))
        responses.append((t, 0, arr))

    INF = 10**18
    ans = [INF] * n

    for t, bit_value, arr in responses:
        for i in range(n):
            if ((i >> t) & 1) != bit_value:
                if arr[i] < ans[i]:
                    ans[i] = arr[i]

    sys.stdout.write("-1\n")
    sys.stdout.write(" ".join(map(str, ans)) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()