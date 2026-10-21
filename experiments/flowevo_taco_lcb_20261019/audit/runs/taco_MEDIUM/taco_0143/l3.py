import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1
        a = data[idx:idx + n]
        idx += n

        freq = [0] * (n + 2)
        for value in a:
            freq[value] += 1

        mex = 0
        while mex < len(freq) and freq[mex] > 0:
            mex += 1

        seen = [0] * (n + 2)
        token = 0
        pos = 0
        result = []

        while pos < n:
            if mex == 0:
                # No zero remains, so every following segment has MEX 0.
                # Split into single elements to make the answer as long as possible.
                result.extend([0] * (n - pos))
                break

            token += 1
            need = mex
            count = 0
            right = pos

            # Take the shortest prefix containing all values 0..need-1.
            while right < n and count < need:
                value = a[right]

                if value < need and seen[value] != token:
                    seen[value] = token
                    count += 1

                freq[value] -= 1
                right += 1

            pos = right
            result.append(need)

            mex = 0
            while mex < len(freq) and freq[mex] > 0:
                mex += 1

        output.append(str(len(result)))
        output.append(" ".join(map(str, result)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()