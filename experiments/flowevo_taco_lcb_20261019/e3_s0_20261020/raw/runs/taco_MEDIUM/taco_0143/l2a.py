import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    pos = 1
    output = []

    for _ in range(t):
        n = data[pos]
        pos += 1
        a = data[pos:pos + n]
        pos += n

        # suffix_mex[i] = MEX of a[i:]
        suffix_mex = [0] * (n + 1)
        freq = [0] * (n + 2)
        mex = 0

        for i in range(n - 1, -1, -1):
            x = a[i]
            if x <= n + 1:
                freq[x] += 1

            while mex <= n and freq[mex] > 0:
                mex += 1

            suffix_mex[i] = mex

        answer = []
        left = 0
        segment_freq = [0] * (n + 2)

        while left < n:
            current_mex = suffix_mex[left]

            if current_mex == 0:
                answer.append(0)
                left += 1
                continue

            needed = current_mex
            right = left

            while needed > 0:
                x = a[right]
                if x < current_mex and segment_freq[x] == 0:
                    segment_freq[x] = 1
                    needed -= 1
                right += 1

            answer.append(current_mex)

            for i in range(left, right):
                x = a[i]
                if x < current_mex:
                    segment_freq[x] = 0

            left = right

        output.append(str(len(answer)))
        output.append(" ".join(map(str, answer)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()