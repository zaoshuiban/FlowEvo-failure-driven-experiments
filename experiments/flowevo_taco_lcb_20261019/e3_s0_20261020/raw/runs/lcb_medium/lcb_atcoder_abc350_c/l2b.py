import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    pos = [0] * (n + 1)
    for i, value in enumerate(a):
        pos[value] = i

    ans = []

    for i in range(n):
        target = i + 1
        if a[i] != target:
            j = pos[target]
            old = a[i]

            a[i], a[j] = a[j], a[i]

            pos[target] = i
            pos[old] = j

            ans.append((i + 1, j + 1))

    output = [str(len(ans))]
    output.extend(f"{i} {j}" for i, j in ans)
    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    main()