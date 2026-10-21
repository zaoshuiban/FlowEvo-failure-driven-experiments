import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, K = data[0], data[1]
    R = data[2:2 + N]

    seq = [0] * N
    answers = []

    def dfs(pos, total):
        if pos == N:
            if total % K == 0:
                answers.append(" ".join(map(str, seq)))
            return

        for value in range(1, R[pos] + 1):
            seq[pos] = value
            dfs(pos + 1, total + value)

    dfs(0, 0)

    if answers:
        sys.stdout.write("\n".join(answers) + "\n")

if __name__ == "__main__":
    main()