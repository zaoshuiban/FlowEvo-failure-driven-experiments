import sys

def make_vector(k: int):
    if k == 1:
        return [1]
    if k == 2:
        return [3, 4]
    if k % 2 == 1:
        return [2] * (k - 1) + [k - 2]
    else:
        return [1] * (k - 1) + [(k - 2) // 2]

def main():
    n, m = map(int, sys.stdin.readline().split())

    x = make_vector(n)
    y = make_vector(m)

    ans = []
    for a in x:
        ans.append(" ".join(str(a * b) for b in y))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()