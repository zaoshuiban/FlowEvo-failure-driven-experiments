import sys


class DSU:
    def __init__(self):
        self.parent = list(range(26))
        self.rank = [0] * 26

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    s = data[1]
    t = data[2]

    dsu = DSU()
    answer = []

    for i in range(n):
        a = s[i] - ord('a')
        b = t[i] - ord('a')

        if a != b and dsu.union(a, b):
            answer.append((chr(a + ord('a')), chr(b + ord('a'))))

    output = [str(len(answer))]
    for a, b in answer:
        output.append(f"{a} {b}")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()