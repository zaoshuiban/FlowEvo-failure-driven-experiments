import sys


class FastScanner:
    __slots__ = ("data", "idx", "length")

    def __init__(self):
        self.data = sys.stdin.buffer.read()
        self.idx = 0
        self.length = len(self.data)

    def next_int(self):
        data = self.data
        n = self.length
        i = self.idx

        while i < n and data[i] <= 32:
            i += 1

        num = 0
        while i < n and data[i] > 32:
            num = num * 10 + (data[i] - 48)
            i += 1

        self.idx = i
        return num


def solve():
    fs = FastScanner()
    t = fs.next_int()
    answers = []

    for _ in range(t):
        n = fs.next_int()
        h = fs.next_int()

        diff = [0] * (n + 1)

        for _ in range(n):
            l = fs.next_int()
            r = fs.next_int()
            diff[l] += 1
            diff[r + 1] -= 1

        current = 0
        for i in range(n):
            current += diff[i]
            diff[i] = current

        window_sum = 0
        for i in range(h):
            window_sum += diff[i]

        max_empty = window_sum
        limit = n - h

        for start in range(1, limit + 1):
            window_sum += diff[start + h - 1] - diff[start - 1]
            if window_sum > max_empty:
                max_empty = window_sum

        answers.append(str(n * h - max_empty))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()